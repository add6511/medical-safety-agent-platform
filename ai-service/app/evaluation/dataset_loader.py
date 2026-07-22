"""
评测数据集加载器
从 JSON 文件加载合成评测用例

安全声明：所有数据均为合成教学数据，不使用真实病例。
"""

import json
import logging
from pathlib import Path
from typing import List

from app.evaluation.models import EvaluationCase

logger = logging.getLogger(__name__)


def load_dataset(path: str) -> List[EvaluationCase]:
    """
    从 JSON 文件加载评测数据集

    Args:
        path: 数据集 JSON 文件路径

    Returns:
        评测用例列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 数据格式错误
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"数据集文件不存在: {path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("数据集文件格式错误：应为 JSON 数组")

    cases: List[EvaluationCase] = []
    for i, item in enumerate(data):
        try:
            case = EvaluationCase(**item)
            cases.append(case)
        except Exception as e:
            raise ValueError(f"第 {i + 1} 条用例解析失败: {e}") from e

    logger.info("数据集加载完成。路径=%s, 用例数=%d", path, len(cases))
    return cases


def load_knowledge_documents(path: str) -> List[dict]:
    """
    从 JSON 文件加载合成知识材料

    Args:
        path: 知识材料 JSON 文件路径

    Returns:
        文档字典列表
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"知识材料文件不存在: {path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("知识材料文件格式错误：应为 JSON 数组")

    logger.info("知识材料加载完成。路径=%s, 文档数=%d", path, len(data))
    return data
