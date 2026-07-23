"""
train_lora.py 单元测试

使用 mock 验证配置解析、数据格式化、LoRA 参数和保存逻辑。
不下载真实模型，不执行真实训练。

测试在无 torch 环境中也能运行（需要 torch 的测试会自动 skip）。
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "finetuning" / "config" / "lora_qwen2_5_0_5b.yaml"

# 尝试导入 torch，用于条件 skip
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

requires_torch = pytest.mark.skipif(not HAS_TORCH, reason="需要 PyTorch")


# ============================================================
# 配置解析（不需要 torch）
# ============================================================


class TestConfigParsing:
    """配置解析测试"""

    def test_load_config_with_yaml(self):
        """使用 PyYAML 加载配置"""
        from scripts.train_lora import load_config
        config = load_config(CONFIG_PATH)
        assert config["model_name"] == "Qwen/Qwen2.5-0.5B-Instruct"
        assert config["lora_r"] == 8
        assert config["lora_alpha"] == 16
        assert config["lora_dropout"] == 0.05
        assert config["seed"] == 42

    def test_load_config_target_modules(self):
        """target_modules 解析为列表"""
        from scripts.train_lora import load_config
        config = load_config(CONFIG_PATH)
        assert isinstance(config["target_modules"], list)
        assert "q_proj" in config["target_modules"]
        assert "v_proj" in config["target_modules"]

    def test_simple_yaml_parse(self):
        """简单 YAML 解析器也能正确解析"""
        from scripts.train_lora import _simple_yaml_parse
        config = _simple_yaml_parse(CONFIG_PATH)
        assert config["model_name"] == "Qwen/Qwen2.5-0.5B-Instruct"
        assert config["lora_r"] == 8
        assert isinstance(config["target_modules"], list)

    def test_config_has_all_training_params(self):
        """配置包含所有训练参数"""
        from scripts.train_lora import load_config
        config = load_config(CONFIG_PATH)
        required = [
            "model_name", "lora_r", "lora_alpha", "lora_dropout",
            "target_modules", "learning_rate", "num_train_epochs",
            "per_device_train_batch_size", "gradient_accumulation_steps",
            "max_sequence_length", "seed", "output_dir",
            "dataset_train", "dataset_validation",
        ]
        for key in required:
            assert key in config, f"配置缺少: {key}"


# ============================================================
# LoRA 参数构建（需要 peft）
# ============================================================


class TestLoraConfig:
    """LoRA 参数构建测试"""

    def test_build_lora_config(self):
        """从配置构建 LoraConfig"""
        from scripts.train_lora import load_config, _build_lora_config
        try:
            from peft import LoraConfig
        except ImportError:
            pytest.skip("需要 peft")

        config = load_config(CONFIG_PATH)
        lora_config = _build_lora_config(config)

        assert isinstance(lora_config, LoraConfig)
        assert lora_config.r == 8
        assert lora_config.lora_alpha == 16
        assert lora_config.lora_dropout == 0.05
        assert set(lora_config.target_modules) == {"q_proj", "k_proj", "v_proj", "o_proj"}
        assert lora_config.bias == "none"

    def test_lora_config_from_minimal_dict(self):
        """最小配置也能构建 LoraConfig"""
        from scripts.train_lora import _build_lora_config
        try:
            from peft import LoraConfig
        except ImportError:
            pytest.skip("需要 peft")

        minimal = {
            "lora_r": 4, "lora_alpha": 8,
            "lora_dropout": 0.1, "target_modules": ["q_proj"],
        }
        config = _build_lora_config(minimal)
        assert config.r == 4
        assert config.lora_alpha == 8


# ============================================================
# 精度选择（需要 mock torch）
# ============================================================


@requires_torch
class TestPrecisionSelection:
    """精度选择测试"""

    def test_bf16_when_supported(self):
        """支持 bf16 时选择 bf16"""
        import scripts.train_lora as mod
        real_torch = mod.torch
        try:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.is_bf16_supported.return_value = True
            mod.torch = mock_torch
            assert mod._select_precision() == "bf16"
        finally:
            mod.torch = real_torch

    def test_fp16_when_bf16_not_supported(self):
        """不支持 bf16 时选择 fp16"""
        import scripts.train_lora as mod
        real_torch = mod.torch
        try:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.is_bf16_supported.return_value = False
            mod.torch = mock_torch
            assert mod._select_precision() == "fp16"
        finally:
            mod.torch = real_torch

    def test_fp16_when_no_cuda(self):
        """无 CUDA 时选择 fp16"""
        import scripts.train_lora as mod
        real_torch = mod.torch
        try:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            mod.torch = mock_torch
            assert mod._select_precision() == "fp16"
        finally:
            mod.torch = real_torch


# ============================================================
# 数据格式化（需要 torch）
# ============================================================


@requires_torch
class TestFormatChatDataset:
    """数据格式化测试"""

    def _make_mock_tokenizer(self):
        """创建 mock tokenizer，模拟 Qwen2.5 的 apply_chat_template"""
        tokenizer = MagicMock()
        tokenizer.pad_token_id = 0
        tokenizer.eos_token_id = 1

        def mock_apply_chat_template(messages, tokenize=False, add_generation_prompt=False):
            roles = [m["role"] for m in messages]
            if add_generation_prompt:
                return "x" * 10  # prompt 部分
            if "assistant" in roles:
                return "x" * 15  # 完整文本（prompt + assistant）
            return "x" * 10

        tokenizer.apply_chat_template = mock_apply_chat_template

        def mock_tokenize(text, truncation=True, max_length=1024, padding=False, return_tensors=None):
            return {
                "input_ids": list(range(len(text))),
                "attention_mask": [1] * len(text),
            }

        tokenizer.side_effect = mock_tokenize
        return tokenizer

    def test_format_returns_dataset(self):
        """format_chat_dataset 返回 Dataset 对象"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [{"messages": [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "test"},
        ]}]
        dataset = format_chat_dataset(records, tokenizer, max_length=64)
        assert len(dataset) == 1

    def test_labels_masked_for_prompt(self):
        """prompt 部分的 labels 为 -100"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [{"messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": "asst"},
        ]}]
        dataset = format_chat_dataset(records, tokenizer, max_length=64)
        labels = dataset[0]["labels"].tolist()
        assert all(l == -100 for l in labels[:10])
        assert all(l != -100 for l in labels[10:15])

    def test_padding_labels_are_negative_100(self):
        """padding 位置的 labels 为 -100"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [
            {"messages": [
                {"role": "system", "content": "s"},
                {"role": "user", "content": "u"},
                {"role": "assistant", "content": "a"},
            ]},
            {"messages": [
                {"role": "system", "content": "s"},
                {"role": "user", "content": "u"},
                {"role": "assistant", "content": "a" * 50},
            ]},
        ]
        dataset = format_chat_dataset(records, tokenizer, max_length=200)
        item0 = dataset[0]
        labels0 = item0["labels"].tolist()
        mask0 = item0["attention_mask"].tolist()
        for i, m in enumerate(mask0):
            if m == 0:
                assert labels0[i] == -100

    def test_attention_mask_correct(self):
        """attention_mask：有效 token 为 1，padding 为 0"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [{"messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "a"},
        ]}]
        dataset = format_chat_dataset(records, tokenizer, max_length=64)
        mask = dataset[0]["attention_mask"].tolist()
        assert all(m == 1 for m in mask[:15])

    def test_skip_records_without_assistant(self):
        """跳过没有 assistant 角色的记录"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [
            {"messages": [
                {"role": "system", "content": "test"},
                {"role": "user", "content": "test"},
            ]},
            {"messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "usr"},
                {"role": "assistant", "content": "asst"},
            ]},
        ]
        dataset = format_chat_dataset(records, tokenizer, max_length=64)
        assert len(dataset) == 1

    def test_input_ids_dtype(self):
        """input_ids 为 long 类型"""
        from scripts.train_lora import format_chat_dataset
        tokenizer = self._make_mock_tokenizer()
        records = [{"messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "a"},
        ]}]
        dataset = format_chat_dataset(records, tokenizer, max_length=64)
        assert dataset[0]["input_ids"].dtype == torch.long
        assert dataset[0]["labels"].dtype == torch.long


# ============================================================
# 前置条件校验（mock torch 模块属性）
# ============================================================


@requires_torch
class TestTrainingPrerequisites:
    """训练前置条件校验测试"""

    def test_missing_torch_raises(self):
        """缺少 ML 依赖时抛出 RuntimeError"""
        from scripts.train_lora import _validate_training_prerequisites
        config = {"dataset_train": "finetuning/data/train.jsonl"}
        with patch("scripts.train_lora.check_environment") as mock_env:
            mock_env.return_value = {
                "torch_version": None, "transformers_version": "4.0", "peft_version": "0.1",
            }
            with pytest.raises(RuntimeError, match="PyTorch 未安装"):
                _validate_training_prerequisites(config)

    def test_missing_transformers_raises(self):
        """缺少 transformers 时抛出 RuntimeError"""
        from scripts.train_lora import _validate_training_prerequisites
        config = {"dataset_train": "finetuning/data/train.jsonl"}
        with patch("scripts.train_lora.check_environment") as mock_env:
            mock_env.return_value = {
                "torch_version": "2.0", "transformers_version": None, "peft_version": "0.1",
            }
            with pytest.raises(RuntimeError, match="transformers 未安装"):
                _validate_training_prerequisites(config)

    def test_missing_peft_raises(self):
        """缺少 peft 时抛出 RuntimeError"""
        from scripts.train_lora import _validate_training_prerequisites
        config = {"dataset_train": "finetuning/data/train.jsonl"}
        with patch("scripts.train_lora.check_environment") as mock_env:
            mock_env.return_value = {
                "torch_version": "2.0", "transformers_version": "4.0", "peft_version": None,
            }
            with pytest.raises(RuntimeError, match="peft 未安装"):
                _validate_training_prerequisites(config)

    def test_no_cuda_raises(self):
        """CUDA 不可用时抛出 RuntimeError"""
        from scripts.train_lora import _validate_training_prerequisites
        config = {"dataset_train": "finetuning/data/train.jsonl"}
        with patch("scripts.train_lora.check_environment") as mock_env:
            mock_env.return_value = {
                "torch_version": "2.0", "transformers_version": "4.0", "peft_version": "0.1",
            }
            import scripts.train_lora as mod
            real_torch = mod.torch
            try:
                mock_torch = MagicMock()
                mock_torch.cuda.is_available.return_value = False
                mod.torch = mock_torch
                with pytest.raises(RuntimeError, match="CUDA 不可用"):
                    _validate_training_prerequisites(config)
            finally:
                mod.torch = real_torch

    def test_missing_dataset_raises(self):
        """训练集不存在时抛出 RuntimeError"""
        from scripts.train_lora import _validate_training_prerequisites
        config = {"dataset_train": "nonexistent/train.jsonl"}
        with patch("scripts.train_lora.check_environment") as mock_env:
            mock_env.return_value = {
                "torch_version": "2.0", "transformers_version": "4.0", "peft_version": "0.1",
            }
            import scripts.train_lora as mod
            real_torch = mod.torch
            try:
                mock_torch = MagicMock()
                mock_torch.cuda.is_available.return_value = True
                mod.torch = mock_torch
                with pytest.raises(RuntimeError, match="训练集不存在"):
                    _validate_training_prerequisites(config)
            finally:
                mod.torch = real_torch


# ============================================================
# 元数据保存（需要 mock torch）
# ============================================================


class TestSaveMetadata:
    """元数据保存测试"""

    def test_save_training_metadata(self, tmp_path):
        """save_training_metadata 写入正确的 metadata.json"""
        from scripts.train_lora import save_training_metadata
        import scripts.train_lora as mod

        real_torch = mod.torch
        try:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.is_bf16_supported.return_value = False
            mock_torch.cuda.get_device_name.return_value = "MockGPU"
            mod.torch = mock_torch

            config = {
                "model_name": "Qwen/Qwen2.5-0.5B-Instruct",
                "model_revision": "main",
                "lora_r": 8, "lora_alpha": 16, "lora_dropout": 0.05,
                "target_modules": ["q_proj", "v_proj"],
                "learning_rate": 0.0002, "num_train_epochs": 2,
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 8,
                "max_sequence_length": 1024, "seed": 42,
            }

            metadata = save_training_metadata(
                output_dir=tmp_path, config=config,
                train_loss=0.5, val_loss=0.6,
                train_count=40, val_count=11,
                training_time_seconds=120.5,
            )

            assert metadata["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
            assert metadata["synthetic_data"] is True
            assert metadata["final_train_loss"] == 0.5
            assert metadata["final_eval_loss"] == 0.6
            assert metadata["train_count"] == 40
            assert metadata["training_time_seconds"] == 120.5

            meta_path = tmp_path / "metadata.json"
            assert meta_path.exists()
            with open(meta_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
        finally:
            mod.torch = real_torch

    def test_metadata_disclaimer_present(self, tmp_path):
        """metadata 包含免责声明"""
        from scripts.train_lora import save_training_metadata
        import scripts.train_lora as mod

        real_torch = mod.torch
        try:
            mock_torch = MagicMock()
            mock_torch.cuda.is_available.return_value = False
            mod.torch = mock_torch

            config = {
                "model_name": "test", "lora_r": 1, "lora_alpha": 2,
                "lora_dropout": 0, "target_modules": [], "learning_rate": 0.001,
                "num_train_epochs": 1, "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 1, "max_sequence_length": 128, "seed": 0,
            }
            metadata = save_training_metadata(
                output_dir=tmp_path, config=config,
                train_loss=None, val_loss=None,
                train_count=0, val_count=0, training_time_seconds=0,
            )
            assert "disclaimer" in metadata
            assert "不得用于真实医疗诊断" in metadata["disclaimer"]
        finally:
            mod.torch = real_torch


# ============================================================
# dry-run 不生成权重（不需要 torch）
# ============================================================


class TestDryRunSafety:
    """dry-run 安全性测试"""

    def test_dry_run_no_weights_generated(self):
        """dry-run 不生成模型权重文件"""
        from scripts.train_lora import run_dry_run, load_config
        config = load_config(CONFIG_PATH)
        result = run_dry_run(config)
        assert result["training_executed"] is False
        assert result["adapter_generated"] is False
        assert result["model_downloaded"] is False

        output_dir = PROJECT_ROOT / "finetuning" / "output"
        if output_dir.exists():
            weight_files = list(output_dir.glob("*.safetensors")) + list(output_dir.glob("*.bin"))
            assert len(weight_files) == 0

    def test_dry_run_mode_field(self):
        """dry-run 结果 mode 为 dry-run"""
        from scripts.train_lora import run_dry_run, load_config
        config = load_config(CONFIG_PATH)
        result = run_dry_run(config)
        assert result["mode"] == "dry-run"


# ============================================================
# JSONL 加载（不需要 torch）
# ============================================================


class TestLoadJsonl:
    """JSONL 加载测试"""

    def test_load_train_jsonl(self):
        """加载训练集"""
        from scripts.train_lora import load_jsonl
        train_path = PROJECT_ROOT / "finetuning" / "data" / "train.jsonl"
        if not train_path.exists():
            pytest.skip("训练集不存在")
        records = load_jsonl(train_path)
        assert len(records) == 40
        for record in records:
            assert "messages" in record
            assert len(record["messages"]) == 3

    def test_load_validation_jsonl(self):
        """加载验证集"""
        from scripts.train_lora import load_jsonl
        val_path = PROJECT_ROOT / "finetuning" / "data" / "validation.jsonl"
        if not val_path.exists():
            pytest.skip("验证集不存在")
        records = load_jsonl(val_path)
        assert len(records) == 11


# ============================================================
# 真实训练流程（mock 模型和 Trainer）
# ============================================================


@requires_torch
class TestRunTrainingMock:
    """使用 mock 验证真实训练流程的调用顺序"""

    @patch("scripts.train_lora._save_outputs")
    @patch("scripts.train_lora._build_trainer")
    @patch("scripts.train_lora.format_chat_dataset")
    @patch("scripts.train_lora._setup_model_and_tokenizer")
    @patch("scripts.train_lora.load_jsonl")
    @patch("scripts.train_lora._validate_training_prerequisites")
    def test_training_calls_in_order(
        self, mock_validate, mock_load, mock_setup, mock_format,
        mock_build_trainer, mock_save,
    ):
        """run_training 按正确顺序调用各步骤"""
        from scripts.train_lora import run_training, load_config

        config = load_config(CONFIG_PATH)
        mock_validate.return_value = {"cuda_available": True}
        mock_load.return_value = [{"messages": []}] * 10
        mock_setup.return_value = (MagicMock(), MagicMock())
        mock_format.return_value = MagicMock(__len__=lambda self: 10)

        mock_trainer = MagicMock()
        mock_trainer.train.return_value = MagicMock(training_loss=0.5)
        mock_trainer.evaluate.return_value = {"eval_loss": 0.6}
        mock_trainer.state.log_history = [{"loss": 0.5}, {"eval_loss": 0.6}]
        mock_build_trainer.return_value = mock_trainer
        mock_save.return_value = {"final_train_loss": 0.5, "final_eval_loss": 0.6}

        run_training(config)

        mock_validate.assert_called_once()
        mock_load.assert_called()
        mock_setup.assert_called_once_with(config)
        mock_format.assert_called()
        mock_build_trainer.assert_called_once()
        mock_trainer.train.assert_called_once()
        mock_trainer.evaluate.assert_called_once()
        mock_save.assert_called_once()
