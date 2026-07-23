"""
微调数据集验证脚本

校验 JSONL 文件格式、消息角色、assistant 输出 JSON 合法性、
必要字段完整性、PII 检测和 manifest 一致性。
"""

import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "finetuning" / "data"

REQUIRED_ASSISTANT_FIELDS = [
    "symptom_summary", "red_flags", "risk_level",
    "missing_information", "followup_questions", "disclaimer",
]

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# PII 检测模式
_PII_PATTERNS = {
    "phone": re.compile(r"1[3-9]\d{9}"),
    "id_number": re.compile(r"\d{17}[\dXx]"),
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "bank_card": re.compile(r"\d{16,19}"),
}


def validate_jsonl(path: Path) -> list[str]:
    """验证 JSONL 文件"""
    errors = []
    if not path.exists():
        errors.append(f"文件不存在: {path}")
        return errors

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"行 {line_num}: JSON 解析失败: {e}")
                continue

            # 检查 messages 字段
            messages = record.get("messages")
            if not isinstance(messages, list):
                errors.append(f"行 {line_num}: 缺少 messages 列表")
                continue

            # 检查角色完整性
            roles = [m.get("role") for m in messages]
            for required_role in ("system", "user", "assistant"):
                if required_role not in roles:
                    errors.append(f"行 {line_num}: 缺少 {required_role} 角色")

            # 检查 assistant 输出
            for msg in messages:
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    try:
                        assistant_data = json.loads(content)
                    except json.JSONDecodeError as e:
                        errors.append(f"行 {line_num}: assistant 输出非法 JSON: {e}")
                        continue

                    # 检查必要字段
                    for field in REQUIRED_ASSISTANT_FIELDS:
                        if field not in assistant_data:
                            errors.append(f"行 {line_num}: assistant 输出缺少字段 {field}")

                    # 检查 risk_level 合法性
                    risk = assistant_data.get("risk_level", "")
                    if risk not in VALID_RISK_LEVELS:
                        errors.append(f"行 {line_num}: risk_level 不合法: {risk}")

                    # 检查 disclaimer 存在
                    disclaimer = assistant_data.get("disclaimer", "")
                    if not disclaimer:
                        errors.append(f"行 {line_num}: disclaimer 为空")

                # PII 检测（user 和 system 消息）
                if msg.get("role") in ("user", "system"):
                    content = msg.get("content", "")
                    for pii_name, pattern in _PII_PATTERNS.items():
                        if pattern.search(content):
                            errors.append(f"行 {line_num}: 检测到 {pii_name} 类型 PII")

            # 检查 user 消息不泄露标签
            for msg in messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if "expected_min_risk" in content or "expected_risk" in content:
                        errors.append(f"行 {line_num}: user 消息泄露了期望标签")

    return errors


def validate_manifest(manifest_path: Path) -> list[str]:
    """验证 manifest 文件"""
    errors = []
    if not manifest_path.exists():
        errors.append(f"manifest 不存在: {manifest_path}")
        return errors

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not manifest.get("synthetic_data"):
        errors.append("synthetic_data 不为 true")

    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "validation.jsonl"

    if train_path.exists():
        # 验证 SHA-256
        h = hashlib.sha256()
        with open(train_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        if h.hexdigest() != manifest.get("train_sha256"):
            errors.append("train.jsonl SHA-256 不匹配")

        # 验证数量
        with open(train_path, "r", encoding="utf-8") as f:
            actual_count = sum(1 for line in f if line.strip())
        if actual_count != manifest.get("train_count"):
            errors.append(f"train 数量不匹配: 实际={actual_count}, manifest={manifest.get('train_count')}")

    if val_path.exists():
        h = hashlib.sha256()
        with open(val_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        if h.hexdigest() != manifest.get("validation_sha256"):
            errors.append("validation.jsonl SHA-256 不匹配")

        with open(val_path, "r", encoding="utf-8") as f:
            actual_count = sum(1 for line in f if line.strip())
        if actual_count != manifest.get("validation_count"):
            errors.append(f"validation 数量不匹配: 实际={actual_count}, manifest={manifest.get('validation_count')}")

    return errors


def main():
    all_errors = []

    train_path = DATA_DIR / "train.jsonl"
    val_path = DATA_DIR / "validation.jsonl"
    manifest_path = DATA_DIR / "dataset_manifest.json"

    print("=== 验证训练集 ===")
    train_errors = validate_jsonl(train_path)
    all_errors.extend(train_errors)
    print(f"训练集: {len(train_errors)} 个错误")

    print("\n=== 验证验证集 ===")
    val_errors = validate_jsonl(val_path)
    all_errors.extend(val_errors)
    print(f"验证集: {len(val_errors)} 个错误")

    print("\n=== 验证 manifest ===")
    manifest_errors = validate_manifest(manifest_path)
    all_errors.extend(manifest_errors)
    print(f"manifest: {len(manifest_errors)} 个错误")

    if all_errors:
        print(f"\n共 {len(all_errors)} 个错误:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n所有验证通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()
