"""
LoRA 微调训练入口

支持 --dry-run 模式：
- 不下载模型
- 不加载模型权重
- 不执行训练
- 校验配置和数据集
- 输出预计训练参数和环境状态

安全声明：
- 未执行真实训练时，不得生成 adapter/checkpoint
- 环境不满足时明确写出原因
- 不允许显示"训练成功"
"""

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

logger = logging.getLogger(__name__)

# 延迟导入 torch，允许在无 torch 环境中使用 dry-run 和配置工具
torch = None


def _ensure_torch():
    """确保 torch 已导入，未安装时抛出 RuntimeError"""
    global torch
    if torch is None:
        try:
            import torch as _torch
            torch = _torch
        except ImportError:
            raise RuntimeError(
                "PyTorch 未安装。请运行: pip install -r requirements-finetune.txt"
            )


# ============================================================
# 配置与数据工具
# ============================================================


def load_config(config_path: Path) -> dict:
    """加载 YAML 配置"""
    try:
        import yaml
    except ImportError:
        return _simple_yaml_parse(config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _simple_yaml_parse(path: Path) -> dict:
    """简单 YAML 解析（仅支持扁平键值和列表）"""
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


def check_dataset(config: dict) -> dict:
    """校验数据集文件"""
    train_path = PROJECT_ROOT / config.get("dataset_train", "")
    val_path = PROJECT_ROOT / config.get("dataset_validation", "")

    result = {
        "train_exists": train_path.exists(),
        "validation_exists": val_path.exists(),
        "train_count": 0,
        "validation_count": 0,
    }

    if train_path.exists():
        with open(train_path, "r", encoding="utf-8") as f:
            result["train_count"] = sum(1 for line in f if line.strip())

    if val_path.exists():
        with open(val_path, "r", encoding="utf-8") as f:
            result["validation_count"] = sum(1 for line in f if line.strip())

    return result


def check_environment() -> dict:
    """检查训练环境"""
    import platform

    env = {
        "python_version": platform.python_version(),
        "os": platform.system(),
    }

    try:
        import torch
        env["torch_version"] = torch.__version__
        env["cuda_available"] = torch.cuda.is_available()
        env["gpu_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    except ImportError:
        env["torch_version"] = None
        env["cuda_available"] = False
        env["gpu_count"] = 0

    try:
        import transformers
        env["transformers_version"] = transformers.__version__
    except ImportError:
        env["transformers_version"] = None

    try:
        import peft
        env["peft_version"] = peft.__version__
    except ImportError:
        env["peft_version"] = None

    return env


# ============================================================
# 数据格式化
# ============================================================


def load_jsonl(path: Path) -> list[dict]:
    """加载 JSONL 文件"""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_chat_dataset(records: list[dict], tokenizer, max_length: int):
    """
    将 JSONL messages 格式转换为模型训练所需的 tokenized 格式。

    使用 tokenizer.apply_chat_template 构建输入，对 assistant 回复之外的
    token 将 labels 设为 -100（不计算 loss）。
    """
    _ensure_torch()
    from torch.utils.data import Dataset

    class ChatDataset(Dataset):
        def __init__(self, encodings):
            self.encodings = encodings

        def __len__(self):
            return len(self.encodings["input_ids"])

        def __getitem__(self, idx):
            return {k: v[idx] for k, v in self.encodings.items()}

    input_ids_list = []
    attention_mask_list = []
    labels_list = []

    for record in records:
        messages = record.get("messages", [])
        if not messages:
            continue

        # 提取 system + user 部分和 assistant 部分
        non_assistant_msgs = [m for m in messages if m["role"] != "assistant"]
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]

        if not assistant_msgs:
            continue

        # 使用 apply_chat_template 构建完整输入（带 generation prompt）
        full_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False,
        )

        # 构建 prompt 部分（不含 assistant 回复）
        prompt_messages = non_assistant_msgs
        prompt_text = tokenizer.apply_chat_template(
            prompt_messages, tokenize=False, add_generation_prompt=True,
        )

        # tokenize 完整文本
        full_enc = tokenizer(
            full_text, truncation=True, max_length=max_length,
            padding=False, return_tensors=None,
        )

        # tokenize prompt 部分，用于确定 labels 的掩码位置
        prompt_enc = tokenizer(
            prompt_text, truncation=True, max_length=max_length,
            padding=False, return_tensors=None,
        )

        input_ids = full_enc["input_ids"]
        prompt_len = len(prompt_enc["input_ids"])

        # labels：prompt 部分为 -100，assistant 部分保留
        labels = [-100] * prompt_len + input_ids[prompt_len:]

        input_ids_list.append(input_ids)
        attention_mask_list.append(full_enc["attention_mask"])
        labels_list.append(labels)

    # padding
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    max_len = max(len(ids) for ids in input_ids_list)

    padded_input_ids = []
    padded_attention_mask = []
    padded_labels = []

    for ids, mask, lbl in zip(input_ids_list, attention_mask_list, labels_list):
        pad_len = max_len - len(ids)
        padded_input_ids.append(ids + [pad_token_id] * pad_len)
        padded_attention_mask.append(mask + [0] * pad_len)
        padded_labels.append(lbl + [-100] * pad_len)

    encodings = {
        "input_ids": torch.tensor(padded_input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(padded_attention_mask, dtype=torch.long),
        "labels": torch.tensor(padded_labels, dtype=torch.long),
    }

    return ChatDataset(encodings)


# ============================================================
# 训练元数据保存
# ============================================================


def save_training_metadata(
    output_dir: Path,
    config: dict,
    train_loss: float | None,
    val_loss: float | None,
    train_count: int,
    val_count: int,
    training_time_seconds: float,
):
    """保存训练元数据到 metadata.json"""
    _ensure_torch()

    metadata = {
        "base_model": config["model_name"],
        "model_revision": config.get("model_revision", "main"),
        "dataset_version": "finetune-synthetic-v1",
        "synthetic_data": True,
        "train_count": train_count,
        "validation_count": val_count,
        "seed": config.get("seed", 42),
        "lora_r": config["lora_r"],
        "lora_alpha": config["lora_alpha"],
        "lora_dropout": config["lora_dropout"],
        "target_modules": config["target_modules"],
        "learning_rate": config["learning_rate"],
        "num_train_epochs": config["num_train_epochs"],
        "per_device_train_batch_size": config["per_device_train_batch_size"],
        "gradient_accumulation_steps": config["gradient_accumulation_steps"],
        "max_sequence_length": config["max_sequence_length"],
        "final_train_loss": train_loss,
        "final_eval_loss": val_loss,
        "training_time_seconds": round(training_time_seconds, 2),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
        "precision": "bf16" if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else "fp16",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "本模型为合成教学实验产物，不得用于真实医疗诊断。",
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata


# ============================================================
# dry-run
# ============================================================


def run_dry_run(config: dict):
    """执行 dry-run：校验配置和环境，不下载模型，不训练"""
    print("=== LoRA 微调 dry-run ===\n")

    # 1. 配置信息
    print("--- 配置参数 ---")
    print(f"模型: {config.get('model_name', 'N/A')}")
    print(f"任务类型: {config.get('task_type', 'N/A')}")
    print(f"LoRA r: {config.get('lora_r', 'N/A')}")
    print(f"LoRA alpha: {config.get('lora_alpha', 'N/A')}")
    print(f"LoRA dropout: {config.get('lora_dropout', 'N/A')}")
    print(f"目标模块: {config.get('target_modules', 'N/A')}")
    print(f"学习率: {config.get('learning_rate', 'N/A')}")
    print(f"训练轮数: {config.get('num_train_epochs', 'N/A')}")
    print(f"批次大小: {config.get('per_device_train_batch_size', 'N/A')}")
    print(f"梯度累积步数: {config.get('gradient_accumulation_steps', 'N/A')}")
    print(f"最大序列长度: {config.get('max_sequence_length', 'N/A')}")
    print(f"随机种子: {config.get('seed', 'N/A')}")
    print()

    # 2. 数据集检查
    print("--- 数据集检查 ---")
    dataset_info = check_dataset(config)
    print(f"训练集: {'存在' if dataset_info['train_exists'] else '不存在'} ({dataset_info['train_count']} 条)")
    print(f"验证集: {'存在' if dataset_info['validation_exists'] else '不存在'} ({dataset_info['validation_count']} 条)")
    print()

    # 3. 环境检查
    print("--- 环境检查 ---")
    env = check_environment()
    print(f"Python: {env['python_version']}")
    print(f"PyTorch: {env['torch_version'] or '未安装'}")
    print(f"transformers: {env['transformers_version'] or '未安装'}")
    print(f"peft: {env['peft_version'] or '未安装'}")
    print(f"CUDA: {'可用' if env['cuda_available'] else '不可用'}")
    print(f"GPU 数量: {env['gpu_count']}")
    print()

    # 4. 训练可行性
    reasons = []
    if not env["torch_version"]:
        reasons.append("PyTorch 未安装")
    if not env["transformers_version"]:
        reasons.append("transformers 未安装")
    if not env["peft_version"]:
        reasons.append("peft 未安装")
    if env["torch_version"] and not env["cuda_available"]:
        reasons.append("CUDA 不可用")
    if not dataset_info["train_exists"]:
        reasons.append("训练集文件不存在")

    can_train = len(reasons) == 0

    print("--- 训练可行性 ---")
    print(f"是否可执行训练: {'是' if can_train else '否'}")
    if reasons:
        print("限制原因:")
        for r in reasons:
            print(f"  - {r}")
    print()

    # 5. 预估参数
    if dataset_info["train_count"] > 0:
        epochs = config.get("num_train_epochs", 2)
        batch_size = config.get("per_device_train_batch_size", 1)
        grad_accum = config.get("gradient_accumulation_steps", 8)
        effective_batch = batch_size * grad_accum
        total_steps = (dataset_info["train_count"] * epochs) // effective_batch
        print("--- 预估训练参数 ---")
        print(f"有效批次大小: {effective_batch}")
        print(f"预估总步数: {total_steps}")
        print()

    # 6. 输出结果
    result = {
        "mode": "dry-run",
        "training_executed": False,
        "config": {k: v for k, v in config.items() if k != "system_message"},
        "dataset": dataset_info,
        "environment": env,
        "can_train": can_train,
        "limitation_reasons": reasons,
        "model_downloaded": False,
        "adapter_generated": False,
    }

    print("=== dry-run 完成 ===")
    print("注意: 未执行真实训练，未下载模型，未生成 adapter。")

    return result


# ============================================================
# 真实训练
# ============================================================


def _validate_training_prerequisites(config: dict) -> dict:
    """校验训练前置条件，不满足时抛出 RuntimeError"""
    env = check_environment()

    missing = []
    if not env["torch_version"]:
        missing.append("PyTorch 未安装")
    if not env["transformers_version"]:
        missing.append("transformers 未安装")
    if not env["peft_version"]:
        missing.append("peft 未安装")
    if missing:
        raise RuntimeError(
            f"缺少 ML 依赖: {', '.join(missing)}。"
            f"请运行: pip install -r requirements-finetune.txt"
        )

    _ensure_torch()
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA 不可用。LoRA 微调需要 NVIDIA GPU。"
            "建议在 Google Colab 或 GPU 服务器上执行训练。"
        )

    dataset_info = check_dataset(config)
    if not dataset_info["train_exists"]:
        raise RuntimeError(
            f"训练集不存在: {config.get('dataset_train')}。"
            f"请先运行: python scripts/prepare_finetune_dataset.py"
        )

    return {**env, **dataset_info}


def _build_lora_config(config: dict):
    """从 YAML 配置构建 PEFT LoraConfig"""
    from peft import LoraConfig

    return LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        task_type=config.get("task_type", "CAUSAL_LM"),
        bias="none",
    )


def _select_precision():
    """基于硬件能力自动选择 bf16 或 fp16"""
    _ensure_torch()
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return "bf16"
    return "fp16"


def _setup_model_and_tokenizer(config: dict):
    """加载模型和分词器，应用 LoRA"""
    _ensure_torch()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import get_peft_model

    model_name = config["model_name"]
    revision = config.get("model_revision", "main")

    logger.info("正在加载分词器: %s", model_name)
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        revision=revision,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    precision = _select_precision()
    torch_dtype = torch.bfloat16 if precision == "bf16" else torch.float16
    logger.info("正在加载模型: %s (dtype=%s)", model_name, precision)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        revision=revision,
        torch_dtype=torch_dtype,
        device_map="auto",
    )

    # 启用梯度检查点以节省显存
    model.gradient_checkpointing_enable()
    model.config.use_cache = False  # 梯度检查点与 KV cache 冲突

    # 应用 LoRA
    lora_config = _build_lora_config(config)
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


def _build_trainer(model, tokenizer, config: dict, train_dataset, val_dataset):
    """构建 HuggingFace Trainer"""
    from transformers import Trainer, TrainingArguments

    precision = _select_precision()
    output_dir = str(PROJECT_ROOT / config["output_dir"])

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config["num_train_epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config.get("warmup_ratio", 0.1),
        weight_decay=config.get("weight_decay", 0.01),
        logging_steps=config.get("logging_steps", 10),
        save_strategy=config.get("save_strategy", "epoch"),
        eval_strategy=config.get("evaluation_strategy", "epoch"),
        seed=config["seed"],
        bf16=(precision == "bf16"),
        fp16=(precision == "fp16"),
        report_to="none",
        remove_unused_columns=False,
        dataloader_pin_memory=True,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        save_total_limit=2,
        optim="adamw_torch",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )

    return trainer


def _save_outputs(model, tokenizer, trainer, config: dict, train_count: int, val_count: int, training_time: float):
    """保存 adapter、tokenizer、训练日志、配置副本和 metadata"""
    _ensure_torch()

    output_dir = PROJECT_ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存 LoRA adapter
    logger.info("正在保存 LoRA adapter 到: %s", output_dir)
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    # 保存训练日志
    if trainer.state.log_history:
        log_path = output_dir / "training_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(trainer.state.log_history, f, ensure_ascii=False, indent=2, default=str)

    # 保存配置副本
    config_copy_path = output_dir / "config_used.yaml"
    try:
        import yaml
        with open(config_copy_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        with open(config_copy_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2, default=str)

    # 提取最终损失
    train_loss = None
    val_loss = None
    for entry in reversed(trainer.state.log_history):
        if val_loss is None and "eval_loss" in entry:
            val_loss = entry["eval_loss"]
        if train_loss is None and "loss" in entry:
            train_loss = entry["loss"]
        if train_loss is not None and val_loss is not None:
            break

    # 保存 metadata
    metadata = save_training_metadata(
        output_dir=output_dir,
        config=config,
        train_loss=train_loss,
        val_loss=val_loss,
        train_count=train_count,
        val_count=val_count,
        training_time_seconds=training_time,
    )

    return metadata


def run_training(config: dict):
    """执行真实 LoRA 微调训练"""
    # 1. 校验前置条件
    env_info = _validate_training_prerequisites(config)

    _ensure_torch()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 开始 LoRA 微调训练 ===")
    print(f"模型: {config['model_name']}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"精度: {_select_precision()}")
    print(f"显存: {torch.cuda.get_device_properties(0).total_memory // (1024**2)} MB")
    print()

    # 2. 加载数据
    logger.info("正在加载数据集...")
    train_records = load_jsonl(PROJECT_ROOT / config["dataset_train"])
    val_records = load_jsonl(PROJECT_ROOT / config["dataset_validation"])
    print(f"训练集: {len(train_records)} 条, 验证集: {len(val_records)} 条")

    # 3. 加载模型和分词器
    model, tokenizer = _setup_model_and_tokenizer(config)

    # 4. 格式化数据集
    max_length = config.get("max_sequence_length", 1024)
    logger.info("正在格式化数据集 (max_length=%d)...", max_length)
    train_dataset = format_chat_dataset(train_records, tokenizer, max_length)
    val_dataset = format_chat_dataset(val_records, tokenizer, max_length)
    print(f"训练样本: {len(train_dataset)}, 验证样本: {len(val_dataset)}")

    # 5. 构建 Trainer
    trainer = _build_trainer(model, tokenizer, config, train_dataset, val_dataset)

    # 6. 训练
    print("\n--- 开始训练 ---")
    start_time = time.monotonic()
    train_result = trainer.train()
    training_time = time.monotonic() - start_time
    print(f"\n训练完成，耗时 {training_time:.1f} 秒")
    print(f"最终训练损失: {train_result.training_loss:.4f}")

    # 7. 验证
    print("\n--- 验证评估 ---")
    eval_result = trainer.evaluate()
    print(f"验证损失: {eval_result['eval_loss']:.4f}")

    # 8. 保存
    print("\n--- 保存输出 ---")
    metadata = _save_outputs(
        model, tokenizer, trainer, config,
        train_count=len(train_records),
        val_count=len(val_records),
        training_time=training_time,
    )

    output_dir = str(PROJECT_ROOT / config["output_dir"])
    print(f"\n=== 训练完成 ===")
    print(f"Adapter 保存在: {output_dir}")
    print(f"最终训练损失: {metadata['final_train_loss']}")
    print(f"最终验证损失: {metadata['final_eval_loss']}")
    print(f"元数据: {output_dir}/metadata.json")


# ============================================================
# 入口
# ============================================================


def main():
    parser = argparse.ArgumentParser(description="LoRA 微调训练入口")
    parser.add_argument(
        "--config", type=str,
        default="finetuning/config/lora_qwen2_5_0_5b.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅校验配置和环境，不执行训练",
    )
    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    if args.dry_run:
        result = run_dry_run(config)
        # 写入 dry-run 报告
        report_path = PROJECT_ROOT / "finetuning" / "reports" / "dry_run_result.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"dry-run 报告已写入: {report_path}")
    else:
        try:
            run_training(config)
        except RuntimeError as e:
            print(f"\n训练失败: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n训练异常: {e}")
            logger.exception("训练过程中发生未预期错误")
            sys.exit(1)


if __name__ == "__main__":
    main()
