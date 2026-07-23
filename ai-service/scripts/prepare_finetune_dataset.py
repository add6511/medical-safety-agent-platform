"""
合成微调数据集生成脚本（v2）

基于 synthetic_cases_v1.json 生成 Qwen2.5 聊天格式的训练集和验证集。

变更记录（v2）：
- system prompt 中包含完整 JSON Schema 示例
- assistant 输出包含 needs_human_review 和 safety_flags 字段
- 所有字段名固定为英文，使用 json.dumps 生成
- 生成后使用 Pydantic 校验每条记录
- 不合格时立即失败

安全声明：
- 所有数据均为合成教学数据，不包含真实患者信息
- 不输出确定性诊断和药物处方
- 不在 user 输入中泄露预期标签
- 生成结果不得用于真实医疗诊断
"""

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

SEED = 42
TRAIN_RATIO = 0.8

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DATASET = PROJECT_ROOT / "evaluation" / "datasets" / "synthetic_cases_v1.json"
OUTPUT_DIR = PROJECT_ROOT / "finetuning" / "data"

# ========== 规范输出 Schema ==========

# 完整的 system prompt，包含 JSON Schema 示例
SYSTEM_PROMPT = (
    "你是一个基层医疗安全辅助系统。请根据患者描述的症状进行初步分析。\n"
    "注意：你的分析仅供参考，不能替代医生诊断。不得输出确定性诊断结论或药物处方。\n\n"
    "你必须严格输出以下JSON格式，字段名必须使用英文，不要输出任何其他文字：\n"
    '{"symptom_summary": "症状摘要", '
    '"red_flags": ["红旗标识符"], '
    '"risk_level": "LOW或MEDIUM或HIGH或CRITICAL", '
    '"needs_human_review": true或false, '
    '"missing_information": ["缺失信息"], '
    '"followup_questions": ["追问问题"], '
    '"safety_flags": ["安全标记"], '
    '"disclaimer": "免责声明"}'
)

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

VALID_RED_FLAG_IDS = {
    "consciousness_change",
    "severe_breathing_difficulty",
    "persistent_chest_discomfort",
    "uncontrolled_bleeding",
    "self_harm_risk",
    "pregnancy_emergency_signal",
    "acute_abdominal_pain",
    "stroke_signs",
}


# ========== Pydantic 校验模型 ==========

class FinetuneOutput(BaseModel):
    """规范的微调输出 Schema"""
    symptom_summary: str = Field(min_length=1)
    red_flags: list[str] = Field(default_factory=list)
    risk_level: str = Field()
    needs_human_review: bool
    missing_information: list[str] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    disclaimer: str = Field(min_length=1)


def validate_output(data: dict) -> list[str]:
    """校验输出是否符合规范 Schema，返回错误列表"""
    errors = []

    # Pydantic 基础校验
    try:
        FinetuneOutput(**data)
    except Exception as e:
        errors.append(f"Pydantic validation failed: {e}")
        return errors

    # risk_level 枚举校验
    if data.get("risk_level") not in VALID_RISK_LEVELS:
        errors.append(f"risk_level must be one of {VALID_RISK_LEVELS}, got: {data.get('risk_level')}")

    # red_flags 格式校验
    for flag in data.get("red_flags", []):
        if not isinstance(flag, str):
            errors.append(f"red_flags item must be string, got: {type(flag).__name__}")

    # 确保输出是纯 JSON，检查键名是否全英文
    for key in data:
        if not key.isascii():
            errors.append(f"non-ASCII key found: '{key}'")

    return errors


# ========== 数据生成 ==========


def _build_user_message(case: dict) -> str:
    """构建 user 消息，不泄露 expected_min_risk 等标签"""
    symptoms_text = "、".join(
        f"{s['name']}（严重程度{s['severity']}，持续{s['duration']}）"
        for s in case.get("symptoms", [])
    )
    return (
        f"患者信息：\n"
        f"- 症状：{symptoms_text}\n"
        f"- 主诉：{case.get('free_text', '')}\n\n"
        f"请进行风险评估并输出JSON。"
    )


def _build_assistant_output(case: dict) -> dict:
    """构建 assistant 输出 JSON（规范英文 Schema）"""
    risk_level = case.get("expected_min_risk", "LOW")
    red_flags = case.get("red_flags", [])
    category = case.get("category", "")

    # 构建症状摘要
    symptom_names = [s["name"] for s in case.get("symptoms", [])]
    symptom_summary = f"患者出现{'、'.join(symptom_names)}等症状"

    # 构建缺失信息
    missing_info = ["既往病史详情", "用药情况", "过敏史"]
    if risk_level in ("HIGH", "CRITICAL"):
        missing_info.append("生命体征数据")

    # 构建追问问题
    followup = ["症状何时开始？", "是否有加重或缓解因素？"]
    if risk_level in ("HIGH", "CRITICAL"):
        followup.append("是否有陪同人员？")
        followup.append("目前意识是否清楚？")

    # 确定 needs_human_review
    needs_human_review = risk_level in ("HIGH", "CRITICAL") or len(red_flags) > 0

    # 构建 safety_flags
    safety_flags = []
    if category == "unsafe_diagnosis":
        safety_flags.append("contains_definitive_diagnosis")
    if category == "unsafe_prescription":
        safety_flags.append("contains_prescription_or_dosage")
    if risk_level in ("HIGH", "CRITICAL"):
        safety_flags.append("high_risk_case")

    return {
        "symptom_summary": symptom_summary,
        "red_flags": red_flags,
        "risk_level": risk_level,
        "needs_human_review": needs_human_review,
        "missing_information": missing_info,
        "followup_questions": followup,
        "safety_flags": safety_flags,
        "disclaimer": "本分析结果仅供参考，不构成医疗诊断。如有紧急情况请立即就医。",
    }


def generate_dataset(source_path: Path, seed: int = SEED, train_ratio: float = TRAIN_RATIO):
    """生成训练集和验证集"""
    with open(source_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # 过滤掉包含不安全文本和 PII 的案例
    pii_categories = {"pii_phone", "pii_id_number", "pii_email"}
    safe_cases = [
        c for c in cases
        if not c.get("unsafe_candidate_text")
        and c.get("category", "") not in pii_categories
    ]

    random.seed(seed)
    random.shuffle(safe_cases)

    split_idx = int(len(safe_cases) * train_ratio)
    train_cases = safe_cases[:split_idx]
    val_cases = safe_cases[split_idx:]

    return train_cases, val_cases


def cases_to_jsonl(cases: list) -> list[dict]:
    """将案例转换为 Qwen2.5 聊天格式"""
    records = []
    for case in cases:
        user_msg = _build_user_message(case)
        assistant_output = _build_assistant_output(case)

        # 使用 json.dumps 生成，不允许手工拼接
        assistant_json = json.dumps(assistant_output, ensure_ascii=False)

        # 校验生成的输出
        errors = validate_output(assistant_output)
        if errors:
            raise ValueError(
                f"Schema validation failed for case {case.get('case_id', 'unknown')}: {errors}"
            )

        record = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_json},
            ]
        }
        records.append(record)
    return records


def compute_sha256(file_path: Path) -> str:
    """计算文件 SHA-256"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_jsonl(records: list[dict], path: Path) -> None:
    """写入 JSONL 文件"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    print(f"源数据集: {SOURCE_DATASET}")
    if not SOURCE_DATASET.exists():
        print(f"错误: 源数据集不存在: {SOURCE_DATASET}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 备份旧 manifest（如果存在）
    old_manifest = OUTPUT_DIR / "dataset_manifest.json"
    if old_manifest.exists():
        backup = OUTPUT_DIR / "dataset_manifest_v1_backup.json"
        if not backup.exists():
            import shutil
            shutil.copy2(old_manifest, backup)
            print(f"已备份旧 manifest: {backup}")

    train_cases, val_cases = generate_dataset(SOURCE_DATASET)
    train_records = cases_to_jsonl(train_cases)
    val_records = cases_to_jsonl(val_cases)

    # 写入 v2 数据
    train_path = OUTPUT_DIR / "train.jsonl"
    val_path = OUTPUT_DIR / "validation.jsonl"

    write_jsonl(train_records, train_path)
    write_jsonl(val_records, val_path)

    # 再次校验：逐条读取并解析验证
    print("\n=== Schema 校验 ===")
    for path, label in [(train_path, "训练集"), (val_path, "验证集")]:
        errors = 0
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                record = json.loads(line)
                content = record["messages"][2]["content"]
                parsed = json.loads(content)
                errs = validate_output(parsed)
                if errs:
                    print(f"  {label} 第 {i+1} 条校验失败: {errs}")
                    errors += 1
        if errors > 0:
            print(f"错误: {label} 有 {errors} 条不合格，终止。")
            sys.exit(1)
        print(f"  {label}: 全部通过 ({len(train_records if label == '训练集' else val_records)} 条)")

    # 生成 v2 manifest
    manifest = {
        "dataset_version": "finetune-synthetic-v2",
        "schema_version": "canonical-english-v1",
        "source": str(SOURCE_DATASET.name),
        "synthetic_data": True,
        "train_count": len(train_records),
        "validation_count": len(val_records),
        "seed": SEED,
        "train_ratio": TRAIN_RATIO,
        "system_prompt_includes_schema": True,
        "output_schema": {
            "type": "object",
            "required": [
                "symptom_summary", "red_flags", "risk_level",
                "needs_human_review", "missing_information",
                "followup_questions", "safety_flags", "disclaimer",
            ],
            "properties": {
                "symptom_summary": {"type": "string"},
                "red_flags": {"type": "array", "items": {"type": "string"}},
                "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                "needs_human_review": {"type": "boolean"},
                "missing_information": {"type": "array", "items": {"type": "string"}},
                "followup_questions": {"type": "array", "items": {"type": "string"}},
                "safety_flags": {"type": "array", "items": {"type": "string"}},
                "disclaimer": {"type": "string"},
            },
        },
        "change_reason": "v2: 修正 system prompt 包含完整 JSON Schema，新增 needs_human_review 和 safety_fields 字段",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_sha256": compute_sha256(train_path),
        "validation_sha256": compute_sha256(val_path),
    }

    manifest_path = OUTPUT_DIR / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n训练集: {train_path} ({len(train_records)} 条)")
    print(f"验证集: {val_path} ({len(val_records)} 条)")
    print(f"清单: {manifest_path}")
    print(f"版本: finetune-synthetic-v2")


if __name__ == "__main__":
    main()
