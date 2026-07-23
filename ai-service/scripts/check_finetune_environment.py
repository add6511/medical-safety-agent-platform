"""
微调环境检查脚本

检查当前环境是否满足 LoRA 微调的前置条件。
输出环境报告到 finetuning/reports/environment.json。

不安装任何依赖，不下载模型。
"""

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REPORT_PATH = PROJECT_ROOT / "finetuning" / "reports" / "environment.json"


def check_torch():
    """检查 PyTorch"""
    try:
        import torch
        return {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "gpu_names": [
                torch.cuda.get_device_name(i)
                for i in range(torch.cuda.device_count())
            ] if torch.cuda.is_available() else [],
            "gpu_memory_mb": [
                torch.cuda.get_device_properties(i).total_memory // (1024 * 1024)
                for i in range(torch.cuda.device_count())
            ] if torch.cuda.is_available() else [],
        }
    except ImportError:
        return {
            "installed": False,
            "version": None,
            "cuda_available": False,
            "cuda_version": None,
            "gpu_count": 0,
            "gpu_names": [],
            "gpu_memory_mb": [],
        }


def check_transformers():
    """检查 transformers"""
    try:
        import transformers
        return {"installed": True, "version": transformers.__version__}
    except ImportError:
        return {"installed": False, "version": None}


def check_peft():
    """检查 peft"""
    try:
        import peft
        return {"installed": True, "version": peft.__version__}
    except ImportError:
        return {"installed": False, "version": None}


def check_datasets():
    """检查 datasets"""
    try:
        import datasets
        return {"installed": True, "version": datasets.__version__}
    except ImportError:
        return {"installed": False, "version": None}


def check_accelerate():
    """检查 accelerate"""
    try:
        import accelerate
        return {"installed": True, "version": accelerate.__version__}
    except ImportError:
        return {"installed": False, "version": None}


def check_yaml():
    """检查 PyYAML"""
    try:
        import yaml
        return {"installed": True, "version": yaml.__version__}
    except ImportError:
        return {"installed": False, "version": None}


def determine_training_feasibility(env: dict) -> dict:
    """判断是否满足真实训练条件"""
    reasons = []

    torch_info = env["torch"]
    if not torch_info["installed"]:
        reasons.append("PyTorch 未安装")

    transformers_info = env["transformers"]
    if not transformers_info["installed"]:
        reasons.append("transformers 未安装")

    peft_info = env["peft"]
    if not peft_info["installed"]:
        reasons.append("peft 未安装")

    if torch_info["installed"] and not torch_info["cuda_available"]:
        reasons.append("CUDA 不可用（无 NVIDIA GPU 或驱动未安装）")

    if torch_info["installed"] and torch_info["cuda_available"]:
        for i, mem in enumerate(torch_info["gpu_memory_mb"]):
            if mem < 4096:
                reasons.append(f"GPU {i} 显存不足 ({mem}MB < 4096MB)")

    return {
        "can_train": len(reasons) == 0,
        "reasons": reasons,
    }


def main():
    print("=== 微调环境检查 ===\n")

    env = {
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "torch": check_torch(),
        "transformers": check_transformers(),
        "peft": check_peft(),
        "datasets": check_datasets(),
        "accelerate": check_accelerate(),
        "pyyaml": check_yaml(),
    }

    feasibility = determine_training_feasibility(env)
    env["training_feasibility"] = feasibility
    env["checked_at"] = datetime.now(timezone.utc).isoformat()

    # 打印摘要
    print(f"Python: {env['python_version']}")
    print(f"OS: {env['os']}")
    print(f"PyTorch: {env['torch']['version'] or '未安装'}")
    print(f"transformers: {env['transformers']['version'] or '未安装'}")
    print(f"peft: {env['peft']['version'] or '未安装'}")
    print(f"CUDA: {'可用' if env['torch']['cuda_available'] else '不可用'}")
    if env["torch"]["gpu_names"]:
        for i, name in enumerate(env["torch"]["gpu_names"]):
            mem = env["torch"]["gpu_memory_mb"][i]
            print(f"  GPU {i}: {name} ({mem}MB)")
    print(f"\n是否满足训练条件: {'是' if feasibility['can_train'] else '否'}")
    if feasibility["reasons"]:
        print("不满足原因:")
        for r in feasibility["reasons"]:
            print(f"  - {r}")

    # 写入报告
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(env, f, ensure_ascii=False, indent=2)
    print(f"\n环境报告已写入: {REPORT_PATH}")


if __name__ == "__main__":
    main()
