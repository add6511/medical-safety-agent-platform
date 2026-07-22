"""
评测报告生成器
生成 JSON、CSV 和 Markdown 格式的评测报告

安全声明：报告中不得写"达到真实临床可用水平"等结论。
"""

import csv
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.evaluation.models import CaseResult, EvaluationMetrics, EvaluationReport

logger = logging.getLogger(__name__)


def generate_reports(
    report: EvaluationReport,
    baseline_results: List[CaseResult],
    pipeline_results: List[CaseResult],
    output_dir: str,
) -> None:
    """
    生成所有评测报告文件

    Args:
        report: 评测报告数据
        baseline_results: baseline 用例结果
        pipeline_results: pipeline 用例结果
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成 summary.json
    _write_summary_json(report, output_path / "summary.json")

    # 生成 case_results.csv
    _write_case_results_csv(pipeline_results, output_path / "case_results.csv")

    # 生成 report.md
    _write_report_md(report, baseline_results, pipeline_results, output_path / "report.md")

    logger.info("评测报告已生成。目录=%s", output_dir)


def _write_summary_json(report: EvaluationReport, path: Path) -> None:
    """生成 summary.json"""
    data = report.model_dump()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("summary.json 已生成: %s", path)


def _write_case_results_csv(results: List[CaseResult], path: Path) -> None:
    """生成 case_results.csv"""
    if not results:
        return

    fieldnames = [
        "case_id", "category", "expected_risk", "baseline_risk",
        "final_risk", "matched", "downgrade_blocked", "human_review",
        "citation_count", "safety_flags", "latency_ms", "passed",
    ]

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "case_id": r.case_id,
                "category": r.category,
                "expected_risk": r.expected_risk,
                "baseline_risk": r.baseline_risk,
                "final_risk": r.final_risk,
                "matched": r.matched,
                "downgrade_blocked": r.downgrade_blocked,
                "human_review": r.human_review,
                "citation_count": r.citation_count,
                "safety_flags": "|".join(r.safety_flags),
                "latency_ms": r.latency_ms,
                "passed": r.passed,
            })

    logger.info("case_results.csv 已生成: %s", path)


def _write_report_md(
    report: EvaluationReport,
    baseline_results: List[CaseResult],
    pipeline_results: List[CaseResult],
    path: Path,
) -> None:
    """生成 report.md"""
    bm = report.baseline_metrics
    pm = report.pipeline_metrics

    lines = []
    lines.append("# 合成病例评测报告")
    lines.append("")
    lines.append("## 1. 评测目的")
    lines.append("")
    lines.append("本报告用于评估医疗安全型预问诊AI服务的多Agent安全审核流程在合成教学数据上的表现。")
    lines.append("**所有评测数据均为合成教学数据，不使用真实病例。评测结果不得宣传为真实临床准确率。**")
    lines.append("")

    lines.append("## 2. 数据集组成")
    lines.append("")
    lines.append(f"- 数据集版本: {report.dataset_version}")
    lines.append(f"- 总用例数: {pm.total_cases}")

    # 按类别统计
    category_counts = {}
    for r in pipeline_results:
        category_counts[r.category] = category_counts.get(r.category, 0) + 1
    lines.append("- 用例分类:")
    for cat, count in sorted(category_counts.items()):
        lines.append(f"  - {cat}: {count}")
    lines.append("")

    lines.append("## 3. 测试环境")
    lines.append("")
    lines.append(f"- 规则集版本: {report.ruleset_version}")
    lines.append(f"- 模型版本: {report.model_version}")
    lines.append(f"- Prompt 版本: {report.prompt_version}")
    lines.append(f"- 知识库版本: {report.knowledge_base_version}")
    lines.append(f"- 生成时间: {report.generated_at}")
    lines.append("")

    lines.append("## 4. 基线方法")
    lines.append("")
    lines.append("**unsafe_mock_baseline**: 直接采用 model_suggested_risk，不使用规则引擎保护。")
    lines.append("")
    lines.append("> 注意：unsafe_mock_baseline 是人为构造的消融对照，不代表任何真实大模型能力。")
    lines.append("")

    lines.append("## 5. 多Agent方法")
    lines.append("")
    lines.append("**safety_multi_agent_pipeline**: 使用 RAG 知识检索、确定性规则引擎和多 Agent 安全审核。")
    lines.append("高风险规则不可被模型下调。")
    lines.append("")

    lines.append("## 6. 指标对比")
    lines.append("")
    lines.append("| 指标 | Baseline | Pipeline |")
    lines.append("|------|----------|----------|")
    lines.append(f"| 总用例数 | {bm.total_cases} | {pm.total_cases} |")
    lines.append(f"| 规则匹配召回率 | {bm.rule_match_recall:.2%} | {pm.rule_match_recall:.2%} |")
    lines.append(f"| 高风险召回率 | {bm.high_risk_recall:.2%} | {pm.high_risk_recall:.2%} |")
    lines.append(f"| 高风险假阴性率 | {bm.high_risk_false_negative_rate:.2%} | {pm.high_risk_false_negative_rate:.2%} |")
    lines.append(f"| 人工审核召回率 | {bm.human_review_recall:.2%} | {pm.human_review_recall:.2%} |")
    lines.append(f"| 模型下调拦截率 | {bm.model_downgrade_block_rate:.2%} | {pm.model_downgrade_block_rate:.2%} |")
    lines.append(f"| 引用覆盖率 | {bm.citation_coverage_rate:.2%} | {pm.citation_coverage_rate:.2%} |")
    lines.append(f"| 免责声明覆盖率 | {bm.disclaimer_coverage_rate:.2%} | {pm.disclaimer_coverage_rate:.2%} |")
    lines.append(f"| 不安全输出拦截率 | {bm.unsafe_output_block_rate:.2%} | {pm.unsafe_output_block_rate:.2%} |")
    lines.append(f"| Agent 成功率 | {bm.agent_success_rate:.2%} | {pm.agent_success_rate:.2%} |")
    lines.append(f"| 精确风险匹配率 | {bm.exact_risk_match_rate:.2%} | {pm.exact_risk_match_rate:.2%} |")
    lines.append(f"| 错误用例数 | {bm.error_case_count} | {pm.error_case_count} |")
    lines.append(f"| 平均延迟(ms) | {bm.mean_latency_ms:.2f} | {pm.mean_latency_ms:.2f} |")
    lines.append(f"| P50延迟(ms) | {bm.p50_latency_ms:.2f} | {pm.p50_latency_ms:.2f} |")
    lines.append(f"| P95延迟(ms) | {bm.p95_latency_ms:.2f} | {pm.p95_latency_ms:.2f} |")
    lines.append("")
    lines.append("### 安全指标")
    lines.append("")
    lines.append("| 指标 | Baseline | Pipeline |")
    lines.append("|------|----------|----------|")
    lines.append(f"| 提示词攻击拦截率 | N/A | {pm.prompt_injection_block_rate:.2%} |")
    lines.append(f"| 越权指令拦截率 | N/A | {pm.privilege_escalation_block_rate:.2%} |")
    lines.append(f"| 敏感信息检测率 | N/A | {pm.pii_detection_rate:.2%} |")
    lines.append(f"| 敏感信息泄漏数量 | N/A | {pm.pii_leak_count} |")
    lines.append("")
    lines.append("> 注：安全指标基于规则的教学安全检测，不覆盖所有真实攻击场景。")
    lines.append("")

    # 典型成功案例
    lines.append("## 7. 典型成功案例")
    lines.append("")
    success_cases = [r for r in pipeline_results if r.passed and r.expected_risk in ("HIGH", "CRITICAL")][:5]
    for r in success_cases:
        lines.append(f"- **{r.case_id}** ({r.category}): 预期{r.expected_risk} → 实际{r.final_risk}，"
                     f"下调阻止={r.downgrade_blocked}，人工审核={r.human_review}")
    if not success_cases:
        lines.append("- 无符合条件的成功案例")
    lines.append("")

    # 失败案例
    lines.append("## 8. 失败案例")
    lines.append("")
    failed_cases = [r for r in pipeline_results if not r.passed][:5]
    for r in failed_cases:
        lines.append(f"- **{r.case_id}** ({r.category}): 预期{r.expected_risk} → 实际{r.final_risk}，"
                     f"安全标记={r.safety_flags}")
    if not failed_cases:
        lines.append("- 无失败案例")
    lines.append("")

    lines.append("## 9. 局限性")
    lines.append("")
    lines.append("- 所有数据为合成教学数据，不代表真实临床场景")
    lines.append("- 使用 mock embedding 和内存向量存储，非生产环境配置")
    lines.append("- 规则引擎基于简单的关键字和红旗匹配，非完整临床决策系统")
    lines.append("- 不安全文本检测使用正则表达式，可能存在遗漏或误判")
    lines.append("- 评测结果仅用于教学演示和安全流程验证")
    lines.append("")

    lines.append("## 10. 教学与医疗安全声明")
    lines.append("")
    lines.append("**本报告及所有评测内容仅供教学演示，不构成诊断或治疗建议。**")
    lines.append("")
    lines.append("- 所有病例均为合成教学示例，不包含真实患者数据")
    lines.append("- 评测结果不得宣传为真实临床准确率或临床可用水平")
    lines.append("- 如需就医请咨询专业医疗机构")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("report.md 已生成: %s", path)
