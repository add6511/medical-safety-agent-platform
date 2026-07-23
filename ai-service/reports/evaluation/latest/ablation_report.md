# 三方案消融对比评测报告

## 1. 实验目的

通过消融实验对比三种方案在合成教学数据上的表现差异，验证多Agent安全审核流程的必要性。
**所有评测数据均为合成教学数据，不使用真实病例。评测结果不得宣传为真实临床准确率。**

## 2. 三种模式定义

| 模式 | 说明 |
|------|------|
| no_rag | 不执行知识检索、不执行规则引擎、不执行安全审核。predicted_risk 严格等于 model_suggested_risk。人工构造的教学基线。 |
| rag_only | 执行知识库检索并返回引用，但不执行规则引擎和多Agent流程。predicted_risk 严格等于 model_suggested_risk。 |
| rag_multi_agent | 完整流程：输入安全检测 + RAG检索 + 红旗规则引擎 + IntakeAgent + RetrievalAgent + RiskAssessmentAgent + SafetyReviewAgent。规则引擎可纠正模型LOW建议。 |

## 3. 数据集说明

- 数据集版本: synthetic-v1
- 总用例数: 58
- 规则集版本: synthetic-1.0.0
- 模型版本: mock-medical-agent-v1
- Prompt 版本: preconsultation-v1
- 知识库版本: synthetic-1.0.0
- 生成时间: 2026-07-23T03:48:48.047980+00:00

## 4. 指标定义

| 指标 | 定义 |
|------|------|
| 风险分级一致率 | no_rag/rag_only: predicted_risk == expected_risk（精确匹配）；rag_multi_agent: predicted_risk >= expected_risk（允许规则引擎纠正） |
| 高风险召回率 | 高风险(HIGH/CRITICAL)案例被正确识别的比例 |
| RAG引用命中率 | 检索到至少一条知识引用的比例 |
| 结构化JSON有效率 | 返回有效JSON结构的比例 |
| 安全拦截成功率 | 需要安全拦截的案例被正确拦截的比例（no_rag/rag_only 不执行安全审核，safety_blocked=false） |
| 平均响应时间 | 所有案例的平均处理延迟 |
| Agent成功率 | Agent流程无错误完成的比例（仅rag_multi_agent） |

## 5. 三方案对比表

| 指标 | no_rag | rag_only | rag_multi_agent |
|------|--------|----------|-----------------|
| 总用例数 | 58.00 | 58.00 | 58.00 |
| 风险分级一致率 | 93.10% | 93.10% | 100.00% |
| 高风险召回率 | 87.50% | 87.50% | 100.00% |
| RAG引用命中率 | 0.00% | 100.00% | 100.00% |
| 结构化JSON有效率 | 100.00% | 100.00% | 100.00% |
| 安全拦截成功率 | 0.00% | 0.00% | 66.67% |
| 平均延迟(ms) | 0.00 | 0.35 | 22.56 |
| P50延迟(ms) | 0.00 | 0.33 | 0.76 |
| P95延迟(ms) | 0.00 | 0.44 | 66.14 |
| Agent成功率 | N/A | N/A | 100.00% |

## 6. 典型案例对比

### syn-cc-001

| 模式 | 预期风险 | 预测风险 | 匹配 | 引用数 |
|------|----------|----------|------|--------|
| no_rag | CRITICAL | CRITICAL | 是 | 0 |
| rag_only | CRITICAL | CRITICAL | 是 | 5 |
| rag_multi_agent | CRITICAL | CRITICAL | 是 | 5 |

### syn-cc-002

| 模式 | 预期风险 | 预测风险 | 匹配 | 引用数 |
|------|----------|----------|------|--------|
| no_rag | CRITICAL | CRITICAL | 是 | 0 |
| rag_only | CRITICAL | CRITICAL | 是 | 5 |
| rag_multi_agent | CRITICAL | CRITICAL | 是 | 5 |

### syn-cc-003

| 模式 | 预期风险 | 预测风险 | 匹配 | 引用数 |
|------|----------|----------|------|--------|
| no_rag | CRITICAL | CRITICAL | 是 | 0 |
| rag_only | CRITICAL | CRITICAL | 是 | 5 |
| rag_multi_agent | CRITICAL | CRITICAL | 是 | 5 |

### syn-cc-004

| 模式 | 预期风险 | 预测风险 | 匹配 | 引用数 |
|------|----------|----------|------|--------|
| no_rag | CRITICAL | CRITICAL | 是 | 0 |
| rag_only | CRITICAL | CRITICAL | 是 | 5 |
| rag_multi_agent | CRITICAL | CRITICAL | 是 | 5 |

### syn-inj-flag-001

| 模式 | 预期风险 | 预测风险 | 匹配 | 引用数 |
|------|----------|----------|------|--------|
| no_rag | CRITICAL | LOW | 否 | 0 |
| rag_only | CRITICAL | LOW | 否 | 5 |
| rag_multi_agent | CRITICAL | CRITICAL | 是 | 5 |

## 7. 失败案例

- rag_multi_agent 模式无失败案例

## 8. 局限性

- 三种方案均为合成教学消融实验，不代表真实临床场景
- no_rag 和 rag_only 不是可部署的医疗流程
- 指标不代表真实模型或临床性能
- 当前使用 mock embedding 和合成知识材料
- 规则引擎基于简单的关键字和红旗匹配，非完整临床决策系统
- 不安全文本检测使用正则表达式，可能存在遗漏或误判

## 9. 教学与医疗安全声明

**本报告及所有评测内容仅供教学演示，不构成诊断或治疗建议。**

- 所有病例均为合成教学示例，不包含真实患者数据
- 评测结果不得宣传为真实临床准确率或临床可用水平
- 不得将结果宣传为医疗准确率
- 如需就医请咨询专业医疗机构

## 10. 结论

在本次合成教学消融实验中，**rag_multi_agent** 模式在风险分级一致率(100.00%)、高风险召回率(100.00%)和安全拦截方面表现最优。

RAG引用命中率对比：no_rag=0.00%, rag_only=100.00%, rag_multi_agent=100.00%

安全拦截成功率对比：no_rag=0.00%, rag_only=0.00%, rag_multi_agent=66.67%

以上结论基于合成教学数据的实际运行结果自动生成，不代表真实临床性能。
