"""
RetrievalAgent - 知识检索 Agent
调用 KnowledgeService 进行知识检索，知识库为空时优雅降级
"""

import logging
from typing import Any, Dict, List

from app.agents.base import AgentContext, BaseAgent
from app.services.knowledge_service import KnowledgeService

logger = logging.getLogger(__name__)


class RetrievalAgent(BaseAgent):
    """知识检索 Agent"""

    def __init__(self, knowledge_service: KnowledgeService):
        super().__init__("RetrievalAgent")
        self._knowledge_service = knowledge_service

    def _execute(self, context: AgentContext) -> AgentContext:
        """调用知识库进行检索"""
        # 构建查询文本
        query_parts = []
        for symptom in context.normalized_symptoms:
            query_parts.append(symptom.get("name", ""))
        if context.free_text.strip():
            query_parts.append(context.free_text.strip())

        query = " ".join(query_parts).strip()

        if not query:
            logger.info("无有效查询文本，跳过知识检索。case_id=%s", context.case_id)
            context.retrieved_evidence = []
            return context

        try:
            results = self._knowledge_service.search(query=query, top_k=5)

            evidence: List[Dict[str, Any]] = []
            for r in results:
                evidence.append({
                    "chunk_id": r.get("chunk_id", ""),
                    "document_id": r.get("document_id", ""),
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "publisher": r.get("publisher", ""),
                    "source_url": r.get("source_url", ""),
                    "document_version": r.get("document_version", ""),
                    "chunk_index": r.get("chunk_index", 0),
                })

            context.retrieved_evidence = evidence
            logger.info("知识检索完成。case_id=%s, 结果数=%d", context.case_id, len(evidence))

        except Exception as e:
            # 知识库为空或不可用时优雅降级
            logger.warning("知识检索异常，优雅降级。case_id=%s, error=%s", context.case_id, type(e).__name__)
            context.retrieved_evidence = []

        return context
