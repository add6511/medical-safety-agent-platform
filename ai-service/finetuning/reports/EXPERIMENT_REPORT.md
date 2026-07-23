# 轻量 LoRA 微调实验报告

## 1. 实验目的

探索使用 LoRA（Low-Rank Adaptation）对轻量级开源大语言模型进行微调，使其在基层医疗安全辅助预问诊场景中输出结构化风险评估结果。

**本实验为教学演示，未执行真实训练。所有数据均为合成教学数据。**

## 2. 模型选择及许可证

| 项目 | 说明 |
|------|------|
| 模型 | Qwen/Qwen2.5-0.5B-Instruct |
| 参数量 | ~0.49B |
| 许可证 | Apache-2.0 |
| 特点 | 支持中文，支持结构化 JSON 输出 |
| 局限 | 不是医疗专用模型，未经过医学知识微调 |

**声明：本模型不得用于真实医疗诊断。若未来实际训练，必须记录模型 revision/commit hash。**

## 3. 合成数据来源

- 源数据集：`evaluation/datasets/synthetic_cases_v1.json`
- 所有案例均为合成教学数据，不包含真实患者信息
- 使用固定随机种子 42 划分训练集和验证集（80/20）
- 数据格式：Qwen2.5 聊天格式（system + user + assistant）
- assistant 输出为结构化 JSON，包含风险评估字段

## 4. LoRA 参数

| 参数 | 值 |
|------|-----|
| lora_r | 8 |
| lora_alpha | 16 |
| lora_dropout | 0.05 |
| target_modules | q_proj, k_proj, v_proj, o_proj |
| learning_rate | 0.0002 |
| num_train_epochs | 2 |
| per_device_train_batch_size | 1 |
| gradient_accumulation_steps | 8 |
| max_sequence_length | 1024 |
| seed | 42 |

## 5. 环境检查结果

请运行 `python scripts/check_finetune_environment.py` 查看详细环境报告。

环境报告保存在 `finetuning/reports/environment.json`。

## 6. 已执行命令

```powershell
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

## 7. 是否实际训练

**否。当前阶段仅为实验准备，未执行真实训练。**

- 未下载模型权重
- 未加载模型
- 未执行训练步骤
- 未生成 adapter 或 checkpoint

## 8. 基线与微调后对比表

| 指标 | 基线 | 微调后 |
|------|------|--------|
| JSON 有效率 | 待运行后填写 | N/A |
| 必要字段完整率 | 待运行后填写 | N/A |
| 风险等级一致率 | 待运行后填写 | N/A |
| 免责声明存在率 | 待运行后填写 | N/A |
| 确定性诊断拦截率 | 待运行后填写 | N/A |
| 药物处方拦截率 | 待运行后填写 | N/A |

## 9. 硬件限制

当前环境可能缺少：
- NVIDIA GPU（CUDA 不可用）
- PyTorch、transformers、peft 等 ML 依赖

LoRA 微调对 Qwen2.5-0.5B 的最低要求：
- NVIDIA GPU 显存 >= 4GB
- PyTorch + CUDA
- transformers >= 4.37.0
- peft

## 10. 后续步骤

可在以下环境执行真实训练：

1. **Google Colab**（推荐免费 T4 GPU）
   - 上传 `finetuning/` 目录
   - 安装依赖：`pip install -r requirements-finetune.txt`
   - 执行训练：`python scripts/train_lora.py --config finetuning/config/lora_qwen2_5_0_5b.yaml`

2. **GPU 服务器**
   - 确保 CUDA 可用
   - 执行环境检查：`python scripts/check_finetune_environment.py`
   - 执行训练

3. **训练后评测**
   - 生成基线预测和微调后预测
   - 执行评测：`python scripts/evaluate_finetune_outputs.py`

## 11. 教学与医疗安全声明

**本实验及所有相关内容仅供教学演示，不构成诊断或治疗建议。**

- 所有训练数据均为合成教学示例，不包含真实患者数据
- Qwen2.5-0.5B-Instruct 不是医疗专用模型
- 实验结果不得用于真实医疗诊断
- 未执行真实训练时，不得声称模型已被微调
- 不得将结果宣传为医疗准确率
- 如需就医请咨询专业医疗机构
