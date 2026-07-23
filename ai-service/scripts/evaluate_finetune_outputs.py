"""
Finetune evaluation script (v2).

Strict schema validation - does NOT salvage Chinese keys or dict risk_level.
Tracks raw_json_valid, schema_valid, normalized_valid separately.

Safety: all evaluation based on synthetic teaching data.
"""

import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "finetuning" / "reports"
DATA_DIR = PROJECT_ROOT / "finetuning" / "data"

# Canonical schema required fields
REQUIRED_SCHEMA_FIELDS = [
    "symptom_summary", "red_flags", "risk_level",
    "needs_human_review", "missing_information",
    "followup_questions", "safety_flags", "disclaimer",
]

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# Chinese risk level mapping for normalization only
_ZH_RISK_MAP = {
    "\u9ad8": "HIGH",
    "\u4e2d": "MEDIUM",
    "\u4f4e": "LOW",
    "\u4e25\u91cd": "CRITICAL",
    "\u5371\u6025": "CRITICAL",
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

_DEFINITIVE_DIAGNOSIS_KEYWORDS = [
    "\u786e\u8bca", "\u8bca\u65ad\u4e3a", "\u786e\u5b9a\u662f", "\u80af\u5b9a\u662f", "\u4e00\u5b9a\u662f",
    "definitive diagnosis", "confirmed diagnosis",
]

_PRESCRIPTION_KEYWORDS = [
    "\u5904\u65b9", "\u5f00\u836f", "\u670d\u7528", r"\u6bcf\u65e5.*mg", r"\u53e3\u670d.*\u7247",
    "prescribe", "dosage", r"medication.*\d+",
]

_HIGH_RISK_LEVELS = {"HIGH", "CRITICAL"}


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def check_raw_json_valid(parsed: dict | None) -> bool:
    """Whether the raw output is valid JSON (any structure)."""
    return parsed is not None


def check_schema_valid(parsed: dict | None) -> tuple[bool, str]:
    """
    Strict schema validation. Returns (valid, reason).
    Must have all required fields with correct types, English keys, valid risk_level.
    """
    if parsed is None:
        return False, "parsed_output is null"
    if not isinstance(parsed, dict):
        return False, f"parsed_output is {type(parsed).__name__}, not dict"

    # Check for non-ASCII keys
    for key in parsed:
        if not key.isascii():
            return False, f"non-ASCII key: {key!r}"

    # Check required fields
    missing = [f for f in REQUIRED_SCHEMA_FIELDS if f not in parsed]
    if missing:
        return False, f"missing fields: {missing}"

    # Check risk_level type and value
    risk = parsed.get("risk_level")
    if not isinstance(risk, str):
        return False, f"risk_level is {type(risk).__name__}, not string"
    if risk not in VALID_RISK_LEVELS:
        return False, f"risk_level={risk!r} not in {VALID_RISK_LEVELS}"

    return True, ""


def check_schema_valid_bool(parsed: dict | None) -> bool:
    ok, _ = check_schema_valid(parsed)
    return ok


def extract_risk_level_normalized(parsed: dict | None) -> tuple[str | None, str]:
    """
    Extract risk_level with normalization (heuristic fallback).
    Returns (risk_level, reason). Only for normalized_valid tracking.
    """
    if parsed is None:
        return None, "parsed_output is null"
    if not isinstance(parsed, dict):
        return None, f"not dict"

    # Try standard field
    raw = parsed.get("risk_level")
    if raw is None:
        # Try Chinese field
        raw = parsed.get("\u98ce\u9669\u7b49\u7ea7")
        if raw is not None:
            return None, "risk_level from Chinese key (not schema_valid)"

    if raw is None:
        return None, "risk_level field missing"

    if isinstance(raw, str):
        normalized = raw.strip().upper()
        if normalized in VALID_RISK_LEVELS:
            return normalized, ""
        mapped = _ZH_RISK_MAP.get(raw.strip())
        if mapped:
            return mapped, f"mapped from Chinese: {raw!r}"
        return None, f"unrecognized string: {raw!r}"

    if isinstance(raw, dict):
        return None, f"risk_level is dict"

    if isinstance(raw, list):
        return None, f"risk_level is list"

    if isinstance(raw, (int, float)):
        if raw >= 8:
            return "CRITICAL", f"numeric {raw} -> CRITICAL"
        elif raw >= 6:
            return "HIGH", f"numeric {raw} -> HIGH"
        elif raw >= 4:
            return "MEDIUM", f"numeric {raw} -> MEDIUM"
        else:
            return "LOW", f"numeric {raw} -> LOW"

    return None, f"unsupported type: {type(raw).__name__}"


def check_training_executed() -> bool:
    metadata_path = PROJECT_ROOT / "finetuning" / "output" / "qwen2.5-0.5b-lora" / "metadata.json"
    if not metadata_path.exists():
        return False
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata.get("final_train_loss") is not None
    except (json.JSONDecodeError, OSError):
        return False


def evaluate_predictions(records: list[dict]) -> tuple[dict, list[dict]]:
    """
    Evaluate prediction results with strict schema validation.
    Returns (metrics, case_details).
    """
    if not records:
        return {
            "total": 0, "raw_json_valid_count": 0,
            "raw_json_valid_rate": None, "schema_valid_count": 0,
            "schema_valid_rate": None, "normalized_valid_count": 0,
            "normalized_valid_rate": None,
            "required_field_completeness": None,
            "risk_level_accuracy": None, "disclaimer_presence_rate": None,
            "safety_block_rate": None, "human_review_trigger_rate": None,
            "invalid_count": 0,
        }, []

    total = len(records)
    raw_json_valid = 0
    schema_valid = 0
    normalized_valid = 0
    risk_match = 0
    disclaimer_present = 0
    safety_blocked = 0
    human_review_triggered = 0
    invalid_count = 0

    case_details = []

    for record in records:
        case_id = record.get("case_id", "")
        parsed = record.get("parsed_output")
        raw = record.get("raw_output", "")
        invalid_reason = ""

        # Raw JSON validity
        is_raw_valid = check_raw_json_valid(parsed)
        if is_raw_valid:
            raw_json_valid += 1

        # If parsed is None, try re-parsing from raw_output
        if parsed is None:
            try:
                # Strip markdown fences
                cleaned = raw.strip()
                fence = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
                if fence:
                    cleaned = fence.group(1).strip()
                b_start = cleaned.find("{")
                b_end = cleaned.rfind("}")
                if b_start >= 0 and b_end > b_start:
                    parsed = json.loads(cleaned[b_start:b_end + 1])
                    is_raw_valid = True
                    raw_json_valid += 1
            except (json.JSONDecodeError, TypeError):
                invalid_reason = "JSON parse failed"

        # Strict schema validation
        is_schema_valid, schema_reason = check_schema_valid(parsed)
        if is_schema_valid:
            schema_valid += 1
        elif not invalid_reason and schema_reason:
            invalid_reason = schema_reason

        # Normalized risk extraction
        predicted_risk, norm_reason = extract_risk_level_normalized(parsed)
        if predicted_risk is not None:
            normalized_valid += 1

        expected_risk = _get_expected_risk(record)

        # Risk match (using normalized extraction)
        risk_matched = False
        if predicted_risk is not None and predicted_risk == expected_risk:
            risk_match += 1
            risk_matched = True

        # Disclaimer
        has_disclaimer = False
        if parsed is not None and isinstance(parsed.get("disclaimer"), str) and parsed["disclaimer"]:
            disclaimer_present += 1
            has_disclaimer = True

        # Safety: high risk predicted for high risk expected
        is_high_predicted = predicted_risk in _HIGH_RISK_LEVELS if predicted_risk else False
        is_high_expected = expected_risk in _HIGH_RISK_LEVELS

        if is_high_predicted:
            human_review_triggered += 1
        if is_high_expected and is_high_predicted:
            safety_blocked += 1

        if invalid_reason:
            invalid_count += 1

        case_details.append({
            "case_id": case_id,
            "expected_risk": expected_risk,
            "predicted_risk": predicted_risk,
            "raw_json_valid": is_raw_valid,
            "schema_valid": is_schema_valid,
            "normalized_valid": predicted_risk is not None,
            "risk_matched": risk_matched,
            "disclaimer_present": has_disclaimer,
            "invalid_reason": invalid_reason,
            "raw_output_preview": raw[:200] if raw else "",
        })

    high_risk_expected = sum(1 for r in records if _get_expected_risk(r) in _HIGH_RISK_LEVELS)

    metrics = {
        "total": total,
        "raw_json_valid_count": raw_json_valid,
        "raw_json_valid_rate": raw_json_valid / total,
        "schema_valid_count": schema_valid,
        "schema_valid_rate": schema_valid / total,
        "normalized_valid_count": normalized_valid,
        "normalized_valid_rate": normalized_valid / total,
        "required_field_completeness": schema_valid / total,
        "risk_level_accuracy": risk_match / total,
        "disclaimer_presence_rate": disclaimer_present / total,
        "safety_block_rate": safety_blocked / high_risk_expected if high_risk_expected > 0 else None,
        "human_review_trigger_rate": human_review_triggered / total,
        "invalid_count": invalid_count,
    }

    return metrics, case_details


def _get_expected_risk(record: dict) -> str:
    try:
        expected = json.loads(record.get("expected_output", ""))
        val = expected.get("risk_level", "")
        if isinstance(val, str):
            return val.strip().upper()
    except (json.JSONDecodeError, TypeError):
        pass
    return ""


def generate_case_comparison(
    baseline_records: list[dict],
    finetuned_records: list[dict],
    baseline_details: list[dict],
    finetuned_details: list[dict],
) -> list[dict]:
    comparison = []
    for bl_rec, ft_rec, bl_det, ft_det in zip(
        baseline_records, finetuned_records, baseline_details, finetuned_details
    ):
        comparison.append({
            "case_id": bl_rec.get("case_id", ""),
            "expected_risk": bl_det["expected_risk"],
            "baseline_risk": bl_det["predicted_risk"],
            "finetuned_risk": ft_det["predicted_risk"],
            "baseline_raw_json_valid": bl_det["raw_json_valid"],
            "baseline_schema_valid": bl_det["schema_valid"],
            "finetuned_raw_json_valid": ft_det["raw_json_valid"],
            "finetuned_schema_valid": ft_det["schema_valid"],
            "baseline_match": bl_det["risk_matched"],
            "finetuned_match": ft_det["risk_matched"],
            "baseline_invalid_reason": bl_det["invalid_reason"],
            "finetuned_invalid_reason": ft_det["invalid_reason"],
            "baseline_inference_ms": bl_rec.get("inference_time_ms", 0),
            "finetuned_inference_ms": ft_rec.get("inference_time_ms", 0),
        })
    return comparison


def main():
    baseline_path = DATA_DIR / "baseline_predictions.jsonl"
    finetuned_path = DATA_DIR / "finetuned_predictions.jsonl"

    has_baseline = baseline_path.exists()
    has_finetuned = finetuned_path.exists()
    training_executed = check_training_executed()

    baseline_metrics = None
    finetuned_metrics = None
    baseline_details = []
    finetuned_details = []
    case_comparison = None
    status = "success"
    error_message = ""

    try:
        if has_baseline:
            baseline_records = load_jsonl(baseline_path)
            baseline_metrics, baseline_details = evaluate_predictions(baseline_records)
            print(f"Baseline: {baseline_path} ({baseline_metrics['total']} records)")
        else:
            print(f"Baseline not found: {baseline_path}")

        if has_finetuned:
            finetuned_records = load_jsonl(finetuned_path)
            finetuned_metrics, finetuned_details = evaluate_predictions(finetuned_records)
            print(f"Finetuned: {finetuned_path} ({finetuned_metrics['total']} records)")
        else:
            print(f"Finetuned not found: {finetuned_path}")

        comparison_available = has_baseline and has_finetuned
        if comparison_available:
            case_comparison = generate_case_comparison(
                baseline_records, finetuned_records, baseline_details, finetuned_details,
            )
    except Exception as e:
        status = "failed"
        error_message = f"{type(e).__name__}: {e}"
        comparison_available = False
        traceback.print_exc()

    # Training metadata
    training_info = None
    metadata_path = PROJECT_ROOT / "finetuning" / "output" / "qwen2.5-0.5b-lora" / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                training_info = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    now = datetime.now(timezone.utc).isoformat()

    report = {
        "status": status,
        "error_message": error_message,
        "comparison_available": comparison_available,
        "training_executed": training_executed,
        "baseline_available": has_baseline,
        "finetuned_available": has_finetuned,
        "baseline_metrics": baseline_metrics,
        "finetuned_metrics": finetuned_metrics,
        "training_info": {
            "base_model": training_info.get("base_model") if training_info else None,
            "final_train_loss": training_info.get("final_train_loss") if training_info else None,
            "final_eval_loss": training_info.get("final_eval_loss") if training_info else None,
            "training_time_seconds": training_info.get("training_time_seconds") if training_info else None,
        } if training_info else None,
        "evaluated_at": now,
        "disclaimer": (
            "All evaluation based on synthetic teaching data. "
            "raw_json_valid = output is parseable JSON. "
            "schema_valid = matches canonical English-key schema exactly. "
            "normalized_valid = risk_level extractable via heuristics. "
            "Chinese keys or dict risk_level are NOT schema_valid."
        ),
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "finetune_comparison.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport: {report_path}")

    if case_comparison:
        comparison_path = REPORTS_DIR / "finetune_case_comparison.json"
        with open(comparison_path, "w", encoding="utf-8") as f:
            json.dump(case_comparison, f, ensure_ascii=False, indent=2)
        print(f"Case comparison: {comparison_path}")

    if baseline_details or finetuned_details:
        details_path = REPORTS_DIR / "finetune_case_details.json"
        with open(details_path, "w", encoding="utf-8") as f:
            json.dump({
                "baseline": baseline_details,
                "finetuned": finetuned_details,
            }, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\nStatus: {status}")
    print(f"Training executed: {training_executed}")

    _print_metrics("Baseline", baseline_metrics)
    _print_metrics("Finetuned", finetuned_metrics)
    _print_failures("Baseline failures", baseline_details)
    _print_failures("Finetuned failures", finetuned_details)

    if comparison_available and baseline_metrics and finetuned_metrics:
        print("\n--- Comparison ---")
        for key in ["raw_json_valid_rate", "schema_valid_rate", "normalized_valid_rate",
                     "risk_level_accuracy", "disclaimer_presence_rate",
                     "safety_block_rate", "human_review_trigger_rate"]:
            bl_val = baseline_metrics.get(key)
            ft_val = finetuned_metrics.get(key)
            bl_str = f"{bl_val:.2%}" if bl_val is not None else "N/A"
            ft_str = f"{ft_val:.2%}" if ft_val is not None else "N/A"
            print(f"  {key}: {bl_str} -> {ft_str}")


def _print_metrics(title: str, metrics: dict | None):
    if not metrics:
        return
    print(f"\n--- {title} ---")
    for k, v in metrics.items():
        if k in ("total", "raw_json_valid_count", "schema_valid_count",
                 "normalized_valid_count", "invalid_count"):
            print(f"  {k}: {v}")
        elif v is not None:
            print(f"  {k}: {v:.2%}")
        else:
            print(f"  {k}: N/A")


def _print_failures(title: str, details: list[dict]):
    failures = [d for d in details if d.get("invalid_reason")]
    if not failures:
        return
    print(f"\n--- {title} ({len(failures)} records) ---")
    for f in failures:
        print(f"  {f['case_id']}: {f['invalid_reason']}")


if __name__ == "__main__":
    main()
