r"""
评测命令行入口

用法:
    python -m app.evaluation --dataset evaluation/datasets/synthetic_cases_v1.json --output-dir reports/evaluation/latest
    python -m app.evaluation --dataset evaluation/datasets/synthetic_cases_v1.json --output-dir reports/evaluation/latest --ablation

Windows PowerShell:
    .\.venv\Scripts\python.exe -m app.evaluation --dataset evaluation/datasets/synthetic_cases_v1.json --output-dir reports/evaluation/latest
    .\.venv\Scripts\python.exe -m app.evaluation --dataset evaluation/datasets/synthetic_cases_v1.json --output-dir reports/evaluation/latest --ablation
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# 确保项目根目录在 sys.path 中
_project_root = str(Path(__file__).parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.core.config import settings
from app.evaluation.ablation_report import calculate_ablation_mode_metrics, generate_ablation_reports
from app.evaluation.dataset_loader import load_dataset, load_knowledge_documents
from app.evaluation.metrics import calculate_metrics
from app.evaluation.models import AblationReport, EvaluationReport
from app.evaluation.report import generate_reports
from app.evaluation.runner import run_ablation, run_evaluation
from app.rag.embedding import MockEmbeddingProvider
from app.rag.text_splitter import compute_checksum
from app.rag.vector_store import InMemoryVectorStore
from app.services.knowledge_service import KnowledgeService


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def import_synthetic_knowledge(knowledge_service: KnowledgeService, knowledge_path: str) -> None:
    """导入合成知识材料到知识库"""
    docs = load_knowledge_documents(knowledge_path)
    for doc in docs:
        knowledge_service.import_document(
            title=doc["title"],
            publisher=doc["publisher"],
            source_url=doc["source_url"],
            document_version=doc["document_version"],
            published_at=None,
            content=doc["content"],
        )


def main():
    parser = argparse.ArgumentParser(description="合成病例评测工具")
    parser.add_argument(
        "--dataset",
        required=True,
        help="评测数据集 JSON 文件路径",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/evaluation/latest",
        help="评测报告输出目录",
    )
    parser.add_argument(
        "--knowledge",
        default=None,
        help="合成知识材料 JSON 文件路径（可选）",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="运行三方案消融对比评测（no_rag / rag_only / rag_multi_agent）",
    )

    args = parser.parse_args()
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=== 合成病例评测开始 ===")
    logger.info("数据集: %s", args.dataset)
    logger.info("输出目录: %s", args.output_dir)
    logger.info("消融模式: %s", "是" if args.ablation else "否")

    # 加载数据集
    cases = load_dataset(args.dataset)
    logger.info("加载评测用例: %d", len(cases))

    # 创建知识库服务
    embedding_provider = MockEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
    vector_store = InMemoryVectorStore()
    knowledge_service = KnowledgeService(vector_store, embedding_provider)

    # 导入合成知识材料
    knowledge_path = args.knowledge
    if knowledge_path is None:
        default_knowledge = Path(__file__).parent.parent.parent / "evaluation" / "knowledge" / "synthetic_guidance_v1.json"
        if default_knowledge.exists():
            knowledge_path = str(default_knowledge)

    if knowledge_path:
        import_synthetic_knowledge(knowledge_service, knowledge_path)
        logger.info("合成知识材料已导入")
    else:
        logger.warning("未找到合成知识材料，知识库为空")

    # 运行标准评测
    baseline_results, pipeline_results = run_evaluation(cases, knowledge_service)

    baseline_metrics = calculate_metrics(baseline_results)
    pipeline_metrics = calculate_metrics(pipeline_results)

    report = EvaluationReport(
        dataset_version="synthetic-v1",
        ruleset_version=settings.SAFETY_RULESET_VERSION,
        model_version=settings.MODEL_VERSION,
        prompt_version=settings.PROMPT_VERSION,
        knowledge_base_version=settings.SAFETY_RULESET_VERSION,
        baseline_metrics=baseline_metrics,
        pipeline_metrics=pipeline_metrics,
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer="所有评测数据均为合成教学数据，不使用真实病例。评测结果由程序实际计算，不得宣传为真实临床准确率。unsafe_mock_baseline 是人为构造的消融对照，不代表任何真实大模型能力。",
    )

    generate_reports(report, baseline_results, pipeline_results, args.output_dir)

    print("\n=== 标准评测完成 ===")
    print(f"总用例数: {pipeline_metrics.total_cases}")
    print(f"精确风险匹配率: {pipeline_metrics.exact_risk_match_rate:.2%}")
    print(f"高风险召回率: {pipeline_metrics.high_risk_recall:.2%}")

    # 运行消融评测
    if args.ablation:
        logger.info("=== 开始消融评测 ===")
        ablation_results = run_ablation(cases, knowledge_service)

        # 计算各模式指标
        no_rag_metrics = calculate_ablation_mode_metrics(ablation_results, "no_rag")
        rag_only_metrics = calculate_ablation_mode_metrics(ablation_results, "rag_only")
        multi_agent_metrics = calculate_ablation_mode_metrics(ablation_results, "rag_multi_agent")

        ablation_report = AblationReport(
            dataset_version="synthetic-v1",
            ruleset_version=settings.SAFETY_RULESET_VERSION,
            model_version=settings.MODEL_VERSION,
            prompt_version=settings.PROMPT_VERSION,
            knowledge_base_version=settings.SAFETY_RULESET_VERSION,
            modes=[no_rag_metrics, rag_only_metrics, multi_agent_metrics],
            generated_at=datetime.now(timezone.utc).isoformat(),
            disclaimer=(
                "所有评测数据均为合成教学数据，不使用真实病例。"
                "三种方案均为合成教学消融实验。"
                "no_rag 和 rag_only 不是可部署的医疗流程。"
                "指标不代表真实模型或临床性能。"
                "当前使用 mock embedding 和合成知识材料。"
                "不得将结果宣传为医疗准确率。"
            ),
        )

        generate_ablation_reports(ablation_report, ablation_results, args.output_dir)

        print("\n=== 消融评测完成 ===")
        print(f"no_rag         - 风险匹配: {no_rag_metrics.risk_match_rate:.2%}, 高风险召回: {no_rag_metrics.high_risk_recall:.2%}")
        print(f"rag_only       - 风险匹配: {rag_only_metrics.risk_match_rate:.2%}, 高风险召回: {rag_only_metrics.high_risk_recall:.2%}")
        print(f"rag_multi_agent - 风险匹配: {multi_agent_metrics.risk_match_rate:.2%}, 高风险召回: {multi_agent_metrics.high_risk_recall:.2%}")

    print(f"\n报告已生成至: {args.output_dir}")


if __name__ == "__main__":
    main()
