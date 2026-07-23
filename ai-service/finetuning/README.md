# 轻量 LoRA 微调实验

## 概述

本目录包含使用 LoRA（Low-Rank Adaptation）对 Qwen2.5-0.5B-Instruct 进行微调的实验配置和数据。

**当前状态：仅完成实验准备，未执行真实训练。**

## 目录结构

```
finetuning/
├── config/
│   └── lora_qwen2_5_0_5b.yaml   # LoRA 配置
├── data/
│   ├── train.jsonl               # 训练集（生成）
│   ├── validation.jsonl          # 验证集（生成）
│   └── dataset_manifest.json     # 数据集清单（生成）
├── reports/
│   ├── environment.json          # 环境检查报告（生成）
│   ├── dry_run_result.json       # dry-run 报告（生成）
│   ├── finetune_comparison.json  # 评测对比报告（生成）
│   ├── experiment_status.json    # 实验状态
│   └── EXPERIMENT_REPORT.md      # 实验报告
├── output/                       # 模型输出（gitignore）
└── README.md                     # 本文件
```

## 快速开始

```powershell
cd ai-service

# 1. 生成微调数据集
python scripts/prepare_finetune_dataset.py

# 2. 验证数据集
python scripts/validate_finetune_dataset.py

# 3. 检查环境
python scripts/check_finetune_environment.py

# 4. dry-run（不下载模型，不训练）
python scripts/train_lora.py --config finetuning/config/lora_qwen2_5_0_5b.yaml --dry-run

# 5. 评测（无微调结果时返回 N/A）
python scripts/evaluate_finetune_outputs.py
```

## 真实训练前置条件

- NVIDIA GPU 显存 >= 4GB
- 安装微调依赖：`pip install -r requirements-finetune.txt`
- 网络可访问 HuggingFace（下载模型）

## 安全声明

- 所有数据均为合成教学数据
- Qwen2.5-0.5B-Instruct 不是医疗专用模型
- 实验结果不得用于真实医疗诊断
- 当前未执行真实训练
