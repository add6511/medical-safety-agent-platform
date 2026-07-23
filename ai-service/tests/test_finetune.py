"""
第九阶段测试：轻量 LoRA 微调实验准备

覆盖：数据集生成、JSONL 格式、消息角色、assistant JSON 合法性、
必要字段、PII 检测、manifest 一致性、配置解析、dry-run、
环境报告、评测 N/A、training_executed 不误报。
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "finetuning" / "data"
REPORTS_DIR = PROJECT_ROOT / "finetuning" / "reports"
CONFIG_PATH = PROJECT_ROOT / "finetuning" / "config" / "lora_qwen2_5_0_5b.yaml"


# ============================================================
# 数据集可重复生成
# ============================================================


class TestDatasetReproducibility:
    """数据集可重复生成"""

    def test_generate_twice_same_result(self):
        """两次生成结果一致（固定种子）"""
        from scripts.prepare_finetune_dataset import generate_dataset, cases_to_jsonl

        source = PROJECT_ROOT / "evaluation" / "datasets" / "synthetic_cases_v1.json"
        if not source.exists():
            pytest.skip("源数据集不存在")

        train1, val1 = generate_dataset(source, seed=42)
        train2, val2 = generate_dataset(source, seed=42)

        assert [c["case_id"] for c in train1] == [c["case_id"] for c in train2]
        assert [c["case_id"] for c in val1] == [c["case_id"] for c in val2]


# ============================================================
# JSONL 格式合法
# ============================================================


class TestJsonlFormat:
    """JSONL 格式合法"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        """确保数据集已生成"""
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def test_train_jsonl_parseable(self):
        """训练集每行都是合法 JSON"""
        train_path = DATA_DIR / "train.jsonl"
        with open(train_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    json.loads(line)  # 不应抛出异常

    def test_validation_jsonl_parseable(self):
        """验证集每行都是合法 JSON"""
        val_path = DATA_DIR / "validation.jsonl"
        with open(val_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    json.loads(line)


# ============================================================
# 消息角色完整
# ============================================================


class TestMessageRoles:
    """消息角色完整"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def test_all_records_have_roles(self):
        """每条记录都有 system、user、assistant 角色"""
        train_path = DATA_DIR / "train.jsonl"
        with open(train_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                roles = [m["role"] for m in record["messages"]]
                assert "system" in roles, f"缺少 system 角色"
                assert "user" in roles, f"缺少 user 角色"
                assert "assistant" in roles, f"缺少 assistant 角色"


# ============================================================
# assistant 输出是合法 JSON
# ============================================================


class TestAssistantOutputJson:
    """assistant 输出是合法 JSON"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def test_assistant_content_is_valid_json(self):
        """assistant 消息内容是合法 JSON"""
        train_path = DATA_DIR / "train.jsonl"
        with open(train_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                for msg in record["messages"]:
                    if msg["role"] == "assistant":
                        data = json.loads(msg["content"])
                        assert isinstance(data, dict)


# ============================================================
# 必要字段齐全
# ============================================================


class TestRequiredFields:
    """必要字段齐全"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    REQUIRED = [
        "symptom_summary", "red_flags", "risk_level",
        "needs_human_review", "missing_information", "followup_questions",
        "safety_flags", "disclaimer",
    ]

    def test_all_required_fields_present(self):
        """assistant 输出包含所有必要字段"""
        train_path = DATA_DIR / "train.jsonl"
        with open(train_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                for msg in record["messages"]:
                    if msg["role"] == "assistant":
                        data = json.loads(msg["content"])
                        for field in self.REQUIRED:
                            assert field in data, f"缺少字段: {field}"


# ============================================================
# 数据中没有明显个人敏感信息
# ============================================================


class TestNoPII:
    """数据中没有明显个人敏感信息"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def test_no_phone_numbers(self):
        """不包含手机号"""
        import re
        pattern = re.compile(r"1[3-9]\d{9}")
        for split in ("train.jsonl", "validation.jsonl"):
            path = DATA_DIR / split
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    for msg in record["messages"]:
                        assert not pattern.search(msg["content"]), \
                            f"{split} 行 {line_num}: 检测到手机号"

    def test_no_id_numbers(self):
        """不包含身份证号"""
        import re
        pattern = re.compile(r"\d{17}[\dXx]")
        for split in ("train.jsonl", "validation.jsonl"):
            path = DATA_DIR / split
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    for msg in record["messages"]:
                        assert not pattern.search(msg["content"]), \
                            f"{split} 行 {line_num}: 检测到身份证号"

    def test_no_label_leakage_in_user(self):
        """user 消息不泄露期望标签"""
        for split in ("train.jsonl", "validation.jsonl"):
            path = DATA_DIR / split
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    for msg in record["messages"]:
                        if msg["role"] == "user":
                            assert "expected_min_risk" not in msg["content"], \
                                f"{split} 行 {line_num}: user 消息泄露标签"
                            assert "expected_risk" not in msg["content"], \
                                f"{split} 行 {line_num}: user 消息泄露标签"


# ============================================================
# manifest 数量和 SHA-256 正确
# ============================================================


class TestManifest:
    """manifest 数量和 SHA-256 正确"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def test_manifest_exists(self):
        """manifest 文件存在"""
        assert (DATA_DIR / "dataset_manifest.json").exists()

    def test_manifest_synthetic_data_true(self):
        """synthetic_data 为 true"""
        with open(DATA_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["synthetic_data"] is True

    def test_manifest_train_count_matches(self):
        """训练集数量匹配"""
        with open(DATA_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(DATA_DIR / "train.jsonl", "r", encoding="utf-8") as f:
            actual = sum(1 for line in f if line.strip())
        assert manifest["train_count"] == actual

    def test_manifest_validation_count_matches(self):
        """验证集数量匹配"""
        with open(DATA_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(DATA_DIR / "validation.jsonl", "r", encoding="utf-8") as f:
            actual = sum(1 for line in f if line.strip())
        assert manifest["validation_count"] == actual

    def test_manifest_sha256_matches(self):
        """SHA-256 校验值匹配"""
        with open(DATA_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for filename, key in [("train.jsonl", "train_sha256"), ("validation.jsonl", "validation_sha256")]:
            path = DATA_DIR / filename
            if not path.exists():
                continue
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            assert h.hexdigest() == manifest[key], f"{filename} SHA-256 不匹配"


# ============================================================
# 配置文件可以解析
# ============================================================


class TestConfigParsing:
    """配置文件可以解析"""

    def test_config_file_exists(self):
        """配置文件存在"""
        assert CONFIG_PATH.exists()

    def test_config_parseable(self):
        """配置文件可解析"""
        try:
            import yaml
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except ImportError:
            from scripts.train_lora import _simple_yaml_parse
            config = _simple_yaml_parse(CONFIG_PATH)

        assert config is not None
        assert config.get("model_name") == "Qwen/Qwen2.5-0.5B-Instruct"
        assert config.get("task_type") == "CAUSAL_LM"
        assert config.get("lora_r") == 8
        assert config.get("seed") == 42

    def test_config_has_target_modules(self):
        """配置包含 target_modules 列表"""
        try:
            import yaml
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except ImportError:
            from scripts.train_lora import _simple_yaml_parse
            config = _simple_yaml_parse(CONFIG_PATH)

        targets = config.get("target_modules", [])
        assert isinstance(targets, list)
        assert "q_proj" in targets
        assert "v_proj" in targets


# ============================================================
# dry-run 在未安装 ML 依赖时也能正常输出环境报告
# ============================================================


class TestDryRun:
    """dry-run 相关测试"""

    def test_dry_run_produces_report(self, tmp_path):
        """dry-run 生成报告文件"""
        from scripts.train_lora import load_config, run_dry_run

        config = load_config(CONFIG_PATH)
        result = run_dry_run(config)

        assert result["mode"] == "dry-run"
        assert result["training_executed"] is False
        assert result["adapter_generated"] is False

    def test_dry_run_does_not_generate_model_weights(self):
        """dry-run 不生成新的模型权重文件"""
        # 注意：真实训练后 output 目录已有权重，dry-run 不应新增
        output_dir = PROJECT_ROOT / "finetuning" / "output"
        if output_dir.exists():
            # dry-run 报告中 adapter_generated 应为 False
            from scripts.train_lora import load_config, run_dry_run
            config = load_config(CONFIG_PATH)
            result = run_dry_run(config)
            assert result["adapter_generated"] is False

    def test_dry_run_reports_environment(self):
        """dry-run 输出环境状态"""
        from scripts.train_lora import check_environment
        env = check_environment()
        assert "python_version" in env
        assert "torch_version" in env
        assert "cuda_available" in env


# ============================================================
# 没有微调结果时比较指标返回 N/A
# ============================================================


class TestEvaluateFinetune:
    """微调评测相关测试"""

    def test_no_finetuned_results_returns_na(self):
        """没有微调结果时返回 N/A"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        metrics, details = evaluate_predictions([])
        assert metrics["total"] == 0
        assert metrics["raw_json_valid_rate"] is None
        assert metrics["risk_level_accuracy"] is None
        assert details == []

    def test_evaluate_with_valid_record(self):
        """有效记录的评测结果正确"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        records = [{
            "case_id": "val-000",
            "expected_output": '{"risk_level": "CRITICAL", "symptom_summary": "test", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "test"}',
            "raw_output": '{"risk_level": "CRITICAL"}',
            "parsed_output": {"risk_level": "CRITICAL", "symptom_summary": "test", "red_flags": [], "needs_human_review": False, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "test"},
            "raw_json_valid": True,
            "schema_valid": True,
            "invalid_reason": "",
            "inference_time_ms": 100.0,
            "model_type": "baseline",
        }]
        metrics, details = evaluate_predictions(records)
        assert metrics["total"] == 1
        assert metrics["raw_json_valid_rate"] == 1.0
        assert metrics["risk_level_accuracy"] == 1.0
        assert metrics["disclaimer_presence_rate"] == 1.0
        assert metrics["invalid_count"] == 0
        assert details[0]["risk_matched"] is True
        assert details[0]["invalid_reason"] == ""

    def test_check_training_executed_true(self):
        """metadata 存在且有 train_loss 时返回 True"""
        from scripts.evaluate_finetune_outputs import check_training_executed
        metadata_path = PROJECT_ROOT / "finetuning" / "output" / "qwen2.5-0.5b-lora" / "metadata.json"
        if metadata_path.exists():
            result = check_training_executed()
            assert result is True

    def test_generate_case_comparison(self):
        """逐案例对比生成正确结构"""
        from scripts.evaluate_finetune_outputs import generate_case_comparison
        bl = [{"case_id": "val-000", "expected_output": '{"risk_level": "CRITICAL"}',
               "parsed_output": {"risk_level": "LOW"}, "raw_json_valid": True, "inference_time_ms": 50.0}]
        ft = [{"case_id": "val-000", "expected_output": '{"risk_level": "CRITICAL"}',
               "parsed_output": {"risk_level": "CRITICAL"}, "raw_json_valid": True, "inference_time_ms": 60.0}]
        bl_details = [{"case_id": "val-000", "expected_risk": "CRITICAL", "predicted_risk": "LOW",
                       "raw_json_valid": True, "schema_valid": False, "risk_matched": False,
                       "disclaimer_present": False, "invalid_reason": "risk_level mismatch"}]
        ft_details = [{"case_id": "val-000", "expected_risk": "CRITICAL", "predicted_risk": "CRITICAL",
                       "raw_json_valid": True, "schema_valid": True, "risk_matched": True,
                       "disclaimer_present": False, "invalid_reason": ""}]
        comparison = generate_case_comparison(bl, ft, bl_details, ft_details)
        assert len(comparison) == 1
        assert comparison[0]["expected_risk"] == "CRITICAL"
        assert comparison[0]["baseline_risk"] == "LOW"
        assert comparison[0]["finetuned_risk"] == "CRITICAL"
        assert comparison[0]["baseline_match"] is False
        assert comparison[0]["finetuned_match"] is True

    def test_failed_record_stays_in_denominator(self):
        """失败记录留在总分母中"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        good_parsed = {
            "symptom_summary": "\u5934\u75db\u53d1\u70ed",
            "red_flags": [],
            "risk_level": "HIGH",
            "needs_human_review": True,
            "missing_information": [],
            "followup_questions": [],
            "safety_flags": [],
            "disclaimer": "\u4ec5\u4f9b\u53c2\u8003",
        }
        records = [
            {"case_id": "good",
             "expected_output": json.dumps({"risk_level": "HIGH"}, ensure_ascii=False),
             "raw_output": json.dumps(good_parsed, ensure_ascii=False),
             "parsed_output": good_parsed,
             "raw_json_valid": True, "schema_valid": True, "invalid_reason": "",
             "inference_time_ms": 100.0, "model_type": "baseline"},
            {"case_id": "bad",
             "expected_output": json.dumps({"risk_level": "LOW"}, ensure_ascii=False),
             "raw_output": "not json", "parsed_output": None,
             "raw_json_valid": False, "schema_valid": False, "invalid_reason": "JSON parse failed",
             "inference_time_ms": 100.0, "model_type": "baseline"},
        ]
        metrics, details = evaluate_predictions(records)
        assert metrics["total"] == 2
        assert metrics["raw_json_valid_rate"] == 0.5
        assert metrics["schema_valid_count"] == 1
        assert metrics["invalid_count"] == 1
        assert details[0]["invalid_reason"] == ""
        assert details[1]["invalid_reason"] != ""


# ============================================================
# extract_risk_level 专项测试
# ============================================================


class TestExtractRiskLevel:
    """extract_risk_level_normalized 安全提取测试"""

    def test_normal_string(self):
        """正常字符串风险等级"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": "CRITICAL"})
        assert risk == "CRITICAL"
        assert reason == ""

    def test_case_insensitive(self):
        """大小写不敏感"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, _ = extract_risk_level_normalized({"risk_level": "high"})
        assert risk == "HIGH"

    def test_whitespace_trimmed(self):
        """前后空格被去除"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, _ = extract_risk_level_normalized({"risk_level": "  LOW  "})
        assert risk == "LOW"

    def test_chinese_string(self):
        """中文风险等级通过归一化提取器映射为英文（normalized_valid 通道）"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": "高"})
        assert risk == "HIGH"
        assert "mapped from Chinese" in reason

    def test_nested_dict_with_safety_string(self):
        """嵌套字典不再被归一化提取器处理"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": {"safety": "高", "seriousness": []}})
        assert risk is None

    def test_nested_dict_with_severity_number(self):
        """嵌套字典不再被归一化提取器处理"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": {"severity": 9, "duration": 2}})
        assert risk is None

    def test_nested_dict_with_majority(self):
        """嵌套字典不再被归一化提取器处理"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": {"majority": "高", "minority": "中"}})
        assert risk is None

    def test_nested_dict_with_severe_boolean(self):
        """嵌套字典不再被归一化提取器处理"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": {"severe": True, "moderate": False}})
        assert risk is None

    def test_nested_dict_unrecognizable(self):
        """无法提取的嵌套字典返回 None"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": {"foo": "bar", "baz": 42}})
        assert risk is None
        assert "is dict" in reason

    def test_null_value(self):
        """risk_level 为 null"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": None})
        assert risk is None
        assert "missing" in reason

    def test_list_value(self):
        """risk_level 为 list"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": ["HIGH", "LOW"]})
        assert risk is None
        assert "is list" in reason

    def test_numeric_value(self):
        """risk_level 为数字"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, _ = extract_risk_level_normalized({"risk_level": 8})
        assert risk == "CRITICAL"

    def test_unrecognized_string(self):
        """非法字符串"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"risk_level": "INVALID_LEVEL"})
        assert risk is None
        assert "unrecognized" in reason

    def test_null_parsed_output(self):
        """parsed_output 为 None"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized(None)
        assert risk is None
        assert "null" in reason

    def test_missing_field(self):
        """parsed_output 中缺少 risk_level 字段"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        risk, reason = extract_risk_level_normalized({"symptom_summary": "test"})
        assert risk is None
        assert "missing" in reason

    def test_no_crash_on_dict_input(self):
        """不会因 dict 类型而崩溃（原始 bug 场景）"""
        from scripts.evaluate_finetune_outputs import extract_risk_level_normalized
        # 归一化提取器对 dict 类型返回 None
        parsed = {"risk_level": {"safety": "高", "seriousness": [{"severity": "严重程度10"}]}}
        risk, reason = extract_risk_level_normalized(parsed)
        assert risk is None

    def test_dict_type_error_in_evaluate(self):
        """dict 类型风险等级不会导致 evaluate_predictions 崩溃"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        records = [{
            "case_id": "test",
            "expected_output": '{"risk_level": "CRITICAL"}',
            "raw_output": '{"risk_level": {"safety": "高"}}',
            "parsed_output": {"risk_level": {"safety": "高"}},
            "raw_json_valid": True,
            "schema_valid": False,
            "invalid_reason": "risk_level not string",
            "inference_time_ms": 100.0,
            "model_type": "baseline",
        }]
        # 不应抛出 TypeError
        metrics, details = evaluate_predictions(records)
        assert metrics["total"] == 1
        assert details[0]["predicted_risk"] is None


# ============================================================
# 环境检查脚本可用
# ============================================================


class TestEnvironmentCheck:
    """环境检查脚本可用"""

    def test_check_produces_report(self):
        """环境检查生成报告"""
        from scripts.check_finetune_environment import (
            check_torch, check_transformers, check_peft,
            determine_training_feasibility,
        )
        env = {
            "torch": check_torch(),
            "transformers": check_transformers(),
            "peft": check_peft(),
        }
        feasibility = determine_training_feasibility(env)
        assert "can_train" in feasibility
        assert "reasons" in feasibility

    def test_environment_report_json_structure(self):
        """环境报告 JSON 结构正确"""
        report_path = REPORTS_DIR / "environment.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            assert "python_version" in report
            assert "torch" in report
            assert "training_feasibility" in report


# ============================================================
# 预测文件格式验证
# ============================================================


class TestPredictionFileFormat:
    """预测文件格式验证"""

    REQUIRED_KEYS = [
        "case_id", "expected_output", "raw_output",
        "parsed_output", "raw_json_valid", "schema_valid", "invalid_reason",
        "inference_time_ms", "model_type", "generation_params",
    ]

    def _load_prediction_records(self, filename: str) -> list[dict]:
        path = DATA_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} 不存在")
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def test_baseline_has_required_keys(self):
        """基线预测包含所有必要字段"""
        records = self._load_prediction_records("baseline_predictions.jsonl")
        for record in records:
            for key in self.REQUIRED_KEYS:
                assert key in record, f"缺少字段: {key}"

    def test_finetuned_has_required_keys(self):
        """微调后预测包含所有必要字段"""
        records = self._load_prediction_records("finetuned_predictions.jsonl")
        for record in records:
            for key in self.REQUIRED_KEYS:
                assert key in record, f"缺少字段: {key}"

    def test_baseline_model_type(self):
        """基线预测 model_type 为 baseline"""
        records = self._load_prediction_records("baseline_predictions.jsonl")
        for record in records:
            assert record["model_type"] == "baseline"

    def test_finetuned_model_type(self):
        """微调后预测 model_type 为 finetuned"""
        records = self._load_prediction_records("finetuned_predictions.jsonl")
        for record in records:
            assert record["model_type"] == "finetuned"

    def test_same_case_ids(self):
        """两组预测使用相同 case_id"""
        bl = self._load_prediction_records("baseline_predictions.jsonl")
        ft = self._load_prediction_records("finetuned_predictions.jsonl")
        bl_ids = [r["case_id"] for r in bl]
        ft_ids = [r["case_id"] for r in ft]
        assert bl_ids == ft_ids

    def test_same_expected_outputs(self):
        """两组预测使用相同 expected_output"""
        bl = self._load_prediction_records("baseline_predictions.jsonl")
        ft = self._load_prediction_records("finetuned_predictions.jsonl")
        for b, f in zip(bl, ft):
            assert b["expected_output"] == f["expected_output"]

    def test_inference_time_positive(self):
        """推理时间非负"""
        for filename in ("baseline_predictions.jsonl", "finetuned_predictions.jsonl"):
            records = self._load_prediction_records(filename)
            for record in records:
                assert record["inference_time_ms"] >= 0

    def test_record_count_matches_validation(self):
        """预测记录数等于验证集大小"""
        val_path = DATA_DIR / "validation.jsonl"
        if not val_path.exists():
            pytest.skip("验证集不存在")
        with open(val_path, "r", encoding="utf-8") as f:
            val_count = sum(1 for line in f if line.strip())

        for filename in ("baseline_predictions.jsonl", "finetuned_predictions.jsonl"):
            records = self._load_prediction_records(filename)
            assert len(records) == val_count, f"{filename}: {len(records)} != {val_count}"


# ============================================================
# generate_finetune_predictions 脚本接口
# ============================================================


class TestGeneratePredictionsScript:
    """generate_finetune_predictions 脚本接口测试"""

    def test_script_has_main(self):
        """脚本有 main 函数"""
        from scripts import generate_finetune_predictions
        assert hasattr(generate_finetune_predictions, "main")

    def test_script_has_generate_predictions(self):
        """脚本有 generate_predictions 函数"""
        from scripts import generate_finetune_predictions
        assert hasattr(generate_finetune_predictions, "generate_predictions")

    def test_script_has_extract_json(self):
        """脚本有 JSON 提取函数"""
        from scripts.generate_finetune_predictions import extract_json_from_output
        result = extract_json_from_output('{"risk_level": "LOW", "symptom_summary": "test", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "test"}')
        assert result[0] is not None
        assert result[0]["risk_level"] == "LOW"
        assert result[2] is True  # schema_valid

    def test_extract_json_from_markdown(self):
        """从 markdown 代码块中提取 JSON"""
        from scripts.generate_finetune_predictions import extract_json_from_output
        text = '```json\n{"risk_level": "HIGH", "symptom_summary": "test", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "test"}\n```'
        parsed, raw_json_valid, schema_valid, invalid_reason = extract_json_from_output(text)
        assert parsed is not None
        assert parsed["risk_level"] == "HIGH"
        assert raw_json_valid is True
        assert schema_valid is True

    def test_extract_json_from_noisy_text(self):
        """从含噪声文本中提取 JSON"""
        from scripts.generate_finetune_predictions import extract_json_from_output
        text = 'Here is the result: {"risk_level": "MEDIUM", "symptom_summary": "test", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "test"} done.'
        parsed, raw_json_valid, schema_valid, invalid_reason = extract_json_from_output(text)
        assert parsed is not None
        assert parsed["risk_level"] == "MEDIUM"
        assert raw_json_valid is True
        assert schema_valid is True

    def test_extract_json_invalid(self):
        """无效文本返回 4-tuple with None"""
        from scripts.generate_finetune_predictions import extract_json_from_output
        result = extract_json_from_output("not json at all")
        assert result[0] is None
        assert result[1] is False


# ============================================================
# v2 严格 schema 验证
# ============================================================


class TestSchemaValidation:
    """v2 strict schema validation tests"""

    def test_english_keys_schema_valid(self):
        """English key canonical schema is schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {
            "symptom_summary": "test", "red_flags": [], "risk_level": "LOW",
            "needs_human_review": False, "missing_information": [],
            "followup_questions": [], "safety_flags": [], "disclaimer": "test",
        }
        ok, reason = check_schema_valid(parsed)
        assert ok is True
        assert reason == ""

    def test_chinese_keys_not_schema_valid(self):
        """Chinese field names are NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {"症状": "test", "风险等级": "高"}
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "non-ASCII" in reason

    def test_dict_risk_level_not_schema_valid(self):
        """risk_level as dict is NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {
            "symptom_summary": "test", "red_flags": [], "risk_level": {"safety": "高"},
            "needs_human_review": False, "missing_information": [],
            "followup_questions": [], "safety_flags": [], "disclaimer": "test",
        }
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "not string" in reason

    def test_array_risk_level_not_schema_valid(self):
        """risk_level as array is NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {
            "symptom_summary": "test", "red_flags": [], "risk_level": ["HIGH"],
            "needs_human_review": False, "missing_information": [],
            "followup_questions": [], "safety_flags": [], "disclaimer": "test",
        }
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "not string" in reason

    def test_null_risk_level_not_schema_valid(self):
        """risk_level as null is NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {
            "symptom_summary": "test", "red_flags": [], "risk_level": None,
            "needs_human_review": False, "missing_information": [],
            "followup_questions": [], "safety_flags": [], "disclaimer": "test",
        }
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "not string" in reason

    def test_missing_fields_not_schema_valid(self):
        """Missing required fields are NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {"risk_level": "LOW"}
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "missing fields" in reason

    def test_invalid_risk_level_not_schema_valid(self):
        """Invalid risk_level value is NOT schema_valid"""
        from scripts.evaluate_finetune_outputs import check_schema_valid
        parsed = {
            "symptom_summary": "test", "red_flags": [], "risk_level": "EXTREME",
            "needs_human_review": False, "missing_information": [],
            "followup_questions": [], "safety_flags": [], "disclaimer": "test",
        }
        ok, reason = check_schema_valid(parsed)
        assert ok is False
        assert "EXTREME" in reason

    def test_normalized_not_counted_as_schema_valid(self):
        """Normalized results are NOT counted as schema_valid in metrics"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        # Chinese keys - schema_valid should be False
        records = [{
            "case_id": "test",
            "expected_output": '{"risk_level": "HIGH", "symptom_summary": "t", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "t"}',
            "raw_output": '{"风险等级": "高"}',
            "parsed_output": {"风险等级": "高"},
            "raw_json_valid": True, "schema_valid": False, "invalid_reason": "non-ASCII key",
            "inference_time_ms": 100.0, "model_type": "baseline",
        }]
        metrics, details = evaluate_predictions(records)
        assert metrics["schema_valid_rate"] == 0.0
        assert metrics["raw_json_valid_rate"] == 1.0  # JSON is valid, just wrong schema

    def test_single_failure_does_not_abort(self):
        """Single record failure does not abort entire evaluation"""
        from scripts.evaluate_finetune_outputs import evaluate_predictions
        records = [
            {"case_id": "good", "expected_output": '{"risk_level": "HIGH", "symptom_summary": "t", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "t"}',
             "raw_output": '{"risk_level": "HIGH", "symptom_summary": "t", "red_flags": [], "needs_human_review": false, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "t"}',
             "parsed_output": {"risk_level": "HIGH", "symptom_summary": "t", "red_flags": [], "needs_human_review": False, "missing_information": [], "followup_questions": [], "safety_flags": [], "disclaimer": "t"},
             "raw_json_valid": True, "schema_valid": True, "invalid_reason": "",
             "inference_time_ms": 100.0, "model_type": "baseline"},
            {"case_id": "bad", "expected_output": '{"risk_level": "LOW"}',
             "raw_output": "not json", "parsed_output": None,
             "raw_json_valid": False, "schema_valid": False, "invalid_reason": "JSON parse failed",
             "inference_time_ms": 100.0, "model_type": "baseline"},
        ]
        metrics, details = evaluate_predictions(records)
        assert metrics["total"] == 2
        assert metrics["schema_valid_count"] == 1
        assert metrics["invalid_count"] == 1


# ============================================================
# v2 训练数据 schema 验证
# ============================================================


class TestTrainingDataSchema:
    """v2 training data schema validation"""

    @pytest.fixture(autouse=True)
    def ensure_dataset(self):
        train_path = DATA_DIR / "train.jsonl"
        if not train_path.exists():
            from scripts.prepare_finetune_dataset import main
            main()

    def _get_assistant_outputs(self, filename: str) -> list[dict]:
        path = DATA_DIR / filename
        outputs = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                for msg in record["messages"]:
                    if msg["role"] == "assistant":
                        outputs.append(json.loads(msg["content"]))
        return outputs

    def test_train_all_english_keys(self):
        """All training assistant outputs have English keys"""
        outputs = self._get_assistant_outputs("train.jsonl")
        for i, out in enumerate(outputs):
            for key in out:
                assert key.isascii(), f"train record {i}: non-ASCII key {key!r}"

    def test_validation_all_english_keys(self):
        """All validation assistant outputs have English keys"""
        outputs = self._get_assistant_outputs("validation.jsonl")
        for i, out in enumerate(outputs):
            for key in out:
                assert key.isascii(), f"val record {i}: non-ASCII key {key!r}"

    def test_train_has_needs_human_review(self):
        """All training outputs have needs_human_review field"""
        outputs = self._get_assistant_outputs("train.jsonl")
        for i, out in enumerate(outputs):
            assert "needs_human_review" in out, f"train record {i}: missing needs_human_review"
            assert isinstance(out["needs_human_review"], bool), f"train record {i}: needs_human_review not bool"

    def test_train_has_safety_flags(self):
        """All training outputs have safety_flags field"""
        outputs = self._get_assistant_outputs("train.jsonl")
        for i, out in enumerate(outputs):
            assert "safety_flags" in out, f"train record {i}: missing safety_flags"
            assert isinstance(out["safety_flags"], list), f"train record {i}: safety_flags not list"

    def test_train_risk_level_valid_enum(self):
        """All training risk_level values are valid enums"""
        outputs = self._get_assistant_outputs("train.jsonl")
        valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for i, out in enumerate(outputs):
            assert out.get("risk_level") in valid, f"train record {i}: invalid risk_level {out.get('risk_level')}"

    def test_train_risk_level_is_string(self):
        """All training risk_level values are strings (not dict/list/null)"""
        outputs = self._get_assistant_outputs("train.jsonl")
        for i, out in enumerate(outputs):
            assert isinstance(out.get("risk_level"), str), f"train record {i}: risk_level is {type(out.get('risk_level')).__name__}"

    def test_manifest_version_is_v2(self):
        """Manifest declares v2"""
        manifest_path = DATA_DIR / "dataset_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["dataset_version"] == "finetune-synthetic-v2"


# ============================================================
# 预测输出 schema 验证
# ============================================================


class TestPredictionSchema:
    """Prediction output schema tests"""

    def _load_records(self, filename: str) -> list[dict]:
        path = DATA_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} not found")
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def test_baseline_raw_output_preserved(self):
        """Baseline raw_output is preserved (not empty)"""
        records = self._load_records("baseline_predictions.jsonl")
        for r in records:
            assert r.get("raw_output"), f"{r['case_id']}: raw_output is empty"

    def test_finetuned_raw_output_preserved(self):
        """Finetuned raw_output is preserved (not empty)"""
        records = self._load_records("finetuned_predictions.jsonl")
        for r in records:
            assert r.get("raw_output"), f"{r['case_id']}: raw_output is empty"

    def test_baseline_has_raw_json_valid_field(self):
        """Baseline predictions have raw_json_valid field"""
        records = self._load_records("baseline_predictions.jsonl")
        for r in records:
            assert "raw_json_valid" in r, f"{r['case_id']}: missing raw_json_valid"

    def test_baseline_has_schema_valid_field(self):
        """Baseline predictions have schema_valid field"""
        records = self._load_records("baseline_predictions.jsonl")
        for r in records:
            assert "schema_valid" in r, f"{r['case_id']}: missing schema_valid"

    def test_baseline_has_invalid_reason_field(self):
        """Baseline predictions have invalid_reason field"""
        records = self._load_records("baseline_predictions.jsonl")
        for r in records:
            assert "invalid_reason" in r, f"{r['case_id']}: missing invalid_reason"

    def test_baseline_has_generation_params(self):
        """Baseline predictions have generation_params"""
        records = self._load_records("baseline_predictions.jsonl")
        for r in records:
            assert "generation_params" in r, f"{r['case_id']}: missing generation_params"
            assert "do_sample" in r["generation_params"]
            assert r["generation_params"]["do_sample"] is False

    def test_same_generation_params(self):
        """Baseline and finetuned use same generation parameters"""
        bl = self._load_records("baseline_predictions.jsonl")
        ft = self._load_records("finetuned_predictions.jsonl")
        for b, f in zip(bl, ft):
            assert b.get("generation_params") == f.get("generation_params"), \
                f"{b['case_id']}: generation_params differ"

    def test_schema_valid_record_has_english_keys(self):
        """Records marked schema_valid have English keys only"""
        for filename in ("baseline_predictions.jsonl", "finetuned_predictions.jsonl"):
            records = self._load_records(filename)
            for r in records:
                if r.get("schema_valid") and r.get("parsed_output"):
                    for key in r["parsed_output"]:
                        assert key.isascii(), f"{r['case_id']}: schema_valid but non-ASCII key {key!r}"

    def test_schema_valid_risk_level_is_english_enum(self):
        """Records marked schema_valid have risk_level in {LOW,MEDIUM,HIGH,CRITICAL}"""
        valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for filename in ("baseline_predictions.jsonl", "finetuned_predictions.jsonl"):
            records = self._load_records(filename)
            for r in records:
                if r.get("schema_valid") and r.get("parsed_output"):
                    assert r["parsed_output"]["risk_level"] in valid, \
                        f"{r['case_id']}: schema_valid but risk_level={r['parsed_output']['risk_level']!r}"
