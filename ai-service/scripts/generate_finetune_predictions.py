"""
LoRA fine-tuning prediction generation script.

Generates baseline and finetuned predictions using the validation set
with the canonical English-key JSON schema.

Uses --config to load model name and adapter path from YAML.
Safety: all data is synthetic teaching data, no real patients.
"""

import argparse
import gc
import json
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Must match prepare_finetune_dataset.py exactly
SYSTEM_PROMPT = (
    "\u4f60\u662f\u4e00\u4e2a\u57fa\u5c42\u533b\u7597\u5b89\u5168\u8f85\u52a9\u7cfb\u7edf\u3002\u8bf7\u6839\u636e\u60a3\u8005\u63cf\u8ff0\u7684\u75c7\u72b6\u8fdb\u884c\u521d\u6b65\u5206\u6790\u3002\n"
    "\u6ce8\u610f\uff1a\u4f60\u7684\u5206\u6790\u4ec5\u4f9b\u53c2\u8003\uff0c\u4e0d\u80fd\u66ff\u4ee3\u533b\u751f\u8bca\u65ad\u3002\u4e0d\u5f97\u8f93\u51fa\u786e\u5b9a\u6027\u8bca\u65ad\u7ed3\u8bba\u6216\u836f\u7269\u5904\u65b9\u3002\n\n"
    "\u4f60\u5fc5\u987b\u4e25\u683c\u8f93\u51fa\u4ee5\u4e0bJSON\u683c\u5f0f\uff0c\u5b57\u6bb5\u540d\u5fc5\u987b\u4f7f\u7528\u82f1\u6587\uff0c\u4e0d\u8981\u8f93\u51fa\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\uff1a\n"
    '{"symptom_summary": "\u75c7\u72b6\u6458\u8981", '
    '"red_flags": ["\u7ea2\u65d7\u6807\u8bc6\u7b26"], '
    '"risk_level": "LOW\u6216MEDIUM\u6216HIGH\u6216CRITICAL", '
    '"needs_human_review": true\u6216false, '
    '"missing_information": ["\u7f3a\u5931\u4fe1\u606f"], '
    '"followup_questions": ["\u8ffd\u95ee\u95ee\u9898"], '
    '"safety_flags": ["\u5b89\u5168\u6807\u8bb0"], '
    '"disclaimer": "\u514d\u8d23\u58f0\u660e"}'
)

MAX_NEW_TOKENS = 1024
REQUIRED_SCHEMA_FIELDS = {
    "symptom_summary", "red_flags", "risk_level",
    "needs_human_review", "missing_information",
    "followup_questions", "safety_flags", "disclaimer",
}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def load_config(config_path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        return _simple_yaml_parse(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _simple_yaml_parse(path: Path) -> dict:
    config = {}
    current_key = None
    current_list = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- ") and current_key:
                if current_list is None:
                    current_list = []
                current_list.append(stripped[2:].strip().strip('"'))
                config[current_key] = current_list
                continue
            if ":" in stripped:
                current_list = None
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"')
                if value == "true":
                    value = True
                elif value == "false":
                    value = False
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                config[key] = value
                current_key = key
    return config


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_prompt(tokenizer, user_content: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )


def extract_json_from_output(text: str) -> tuple:
    """
    Returns (parsed_dict_or_None, raw_json_valid, schema_valid, invalid_reason).
    """
    cleaned = text.strip()
    # Strip markdown fences
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    # Strip leading/trailing text around JSON
    b_start = cleaned.find("{")
    b_end = cleaned.rfind("}")
    if b_start == -1 or b_end == -1 or b_end <= b_start:
        return None, False, False, "no JSON object found in output"
    json_str = cleaned[b_start:b_end + 1]
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        return None, False, False, f"JSON parse error: {e}"
    if not isinstance(parsed, dict):
        return parsed, True, False, "output is not a JSON object"
    # Check for non-ASCII keys
    for key in parsed:
        if not key.isascii():
            return parsed, True, False, f"non-ASCII key: {key!r}"
    missing = REQUIRED_SCHEMA_FIELDS - set(parsed.keys())
    if missing:
        return parsed, True, False, f"missing fields: {sorted(missing)}"
    risk = parsed.get("risk_level", "")
    if not isinstance(risk, str) or risk not in VALID_RISK_LEVELS:
        return parsed, True, False, f"invalid risk_level: {risk!r}"
    return parsed, True, True, ""


def generate_predictions(model, tokenizer, records: list[dict], model_type: str) -> list[dict]:
    import torch
    results = []
    total = len(records)
    for idx, record in enumerate(records):
        messages = record.get("messages", [])
        user_content = ""
        expected_output = ""
        for msg in messages:
            if msg["role"] == "user":
                user_content = msg["content"]
            elif msg["role"] == "assistant":
                expected_output = msg["content"]
        case_id = f"val-{idx:03d}"
        prompt = build_prompt(tokenizer, user_content)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        start = time.monotonic()
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        inference_ms = (time.monotonic() - start) * 1000
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        raw_output = tokenizer.decode(new_tokens, skip_special_tokens=True)
        parsed, raw_json_valid, schema_valid, invalid_reason = extract_json_from_output(raw_output)
        result = {
            "case_id": case_id,
            "expected_output": expected_output,
            "raw_output": raw_output,
            "parsed_output": parsed,
            "raw_json_valid": raw_json_valid,
            "schema_valid": schema_valid,
            "invalid_reason": invalid_reason,
            "inference_time_ms": round(inference_ms, 2),
            "model_type": model_type,
            "generation_params": {
                "max_new_tokens": MAX_NEW_TOKENS,
                "do_sample": False,
                "temperature": None,
            },
        }
        results.append(result)
        if (idx + 1) % 5 == 0 or idx + 1 == total:
            print(f"  [{model_type}] {idx + 1}/{total} done")
    return results


def write_jsonl(records: list[dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate finetune predictions")
    parser.add_argument(
        "--config", type=str,
        default="finetuning/config/lora_qwen2_5_0_5b.yaml",
        help="Config YAML path",
    )
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    config_path = PROJECT_ROOT / args.config
    config = load_config(config_path)

    model_name = config["model_name"]
    revision = config.get("model_revision", "main")
    adapter_path = str(PROJECT_ROOT / config["output_dir"])
    val_path = PROJECT_ROOT / config["dataset_validation"]
    output_dir = PROJECT_ROOT / "finetuning" / "data"

    print(f"Loading validation: {val_path}")
    val_records = load_jsonl(val_path)
    print(f"Validation records: {len(val_records)}")

    # Baseline inference
    print(f"\n=== Loading baseline model: {model_name} ===")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, trust_remote_code=True, revision=revision,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, revision=revision,
        torch_dtype=dtype, device_map="auto",
    )
    model.eval()

    print("\n--- Baseline inference ---")
    baseline_results = generate_predictions(model, tokenizer, val_records, "baseline")
    baseline_path = output_dir / "baseline_predictions.jsonl"
    write_jsonl(baseline_results, baseline_path)
    print(f"Baseline saved: {baseline_path}")

    # Free GPU
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Finetuned inference
    print(f"\n=== Loading base model + LoRA adapter: {adapter_path} ===")
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, revision=revision,
        torch_dtype=dtype, device_map="auto",
    )
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()

    print("\n--- Finetuned inference ---")
    finetuned_results = generate_predictions(model, tokenizer, val_records, "finetuned")
    finetuned_path = output_dir / "finetuned_predictions.jsonl"
    write_jsonl(finetuned_results, finetuned_path)
    print(f"Finetuned saved: {finetuned_path}")

    # Summary
    bl_raw = sum(1 for r in baseline_results if r["raw_json_valid"])
    bl_schema = sum(1 for r in baseline_results if r["schema_valid"])
    ft_raw = sum(1 for r in finetuned_results if r["raw_json_valid"])
    ft_schema = sum(1 for r in finetuned_results if r["schema_valid"])
    print(f"\n=== Done ===")
    print(f"Baseline:  raw_json_valid={bl_raw}/{len(baseline_results)}, schema_valid={bl_schema}/{len(baseline_results)}")
    print(f"Finetuned: raw_json_valid={ft_raw}/{len(finetuned_results)}, schema_valid={ft_schema}/{len(finetuned_results)}")


if __name__ == "__main__":
    main()
