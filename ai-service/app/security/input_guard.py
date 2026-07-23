"""
输入安全检测模块
检测提示词攻击、越权指令和敏感信息（PII）

安全声明：本模块使用基于规则的教学安全检测，不得宣传为完整生产级防护。
所有检测模式均为合成教学用途，不覆盖所有真实攻击场景。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# ============================================================
# 提示词攻击检测模式
# ============================================================

# 中文提示词注入
_CN_INJECTION_PATTERNS = [
    re.compile(r"忽略(之前|上面|以上|前面)(的|所有)?(指令|规则|提示|要求|设定)", re.IGNORECASE),
    re.compile(r"无视(系统|安全|所有)(规则|限制|约束|指令)", re.IGNORECASE),
    re.compile(r"输出(系统|你的)(提示词|提示语|指令|规则|system\s*prompt)", re.IGNORECASE),
    re.compile(r"绕过(安全|系统|所有)(检查|规则|限制|约束)", re.IGNORECASE),
    re.compile(r"(关闭|禁用|跳过|取消)(人工|安全|系统)(审核|检查|验证)", re.IGNORECASE),
    re.compile(r"(不要|不准|别)(遵守|遵循|执行|理会)(之前|上面|系统)(的)?(指令|规则)", re.IGNORECASE),
]

# 英文提示词注入
_EN_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|above|prior)\s+(instructions|rules|prompts|directives)", re.IGNORECASE),
    re.compile(r"(reveal|show|display|print|output)\s+(system\s*prompt|instructions|rules)", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|all|security)\s+(rules|checks|filters|restrictions)", re.IGNORECASE),
    re.compile(r"disable\s+(human\s+review|safety|moderation|filtering)", re.IGNORECASE),
    re.compile(r"(forget|disregard|override)\s+(previous|all|above)\s+(instructions|rules)", re.IGNORECASE),
]

# 系统提示词提取尝试
_SYSTEM_PROMPT_EXTRACTION_PATTERNS = [
    re.compile(r"(输出|显示|告诉我|打印|reveal|show|print)\s*(你的|系统|the|system)\s*(系统)?\s*(提示词|prompt|指令|instructions)", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"(你的|your)\s*(初始|initial|系统|system)\s*(指令|instructions|设定)", re.IGNORECASE),
]

# 越权角色指令
_PRIVILEGE_ESCALATION_PATTERNS = [
    re.compile(r"(你现在是|你扮演|你是|假装你是|模拟你是)\s*(医生|主任|专家|管理员|admin|root|system)", re.IGNORECASE),
    re.compile(r"(直接|立刻|马上)\s*(给出|提供|输出)\s*(确定性|明确|最终)\s*(诊断|结论|处方)", re.IGNORECASE),
    re.compile(r"(不经|不经过|跳过|无需)\s*(人工|医生|专业)\s*(审核|复核|确认)\s*(直接|立刻)?\s*(通过|确认|批准)", re.IGNORECASE),
    re.compile(r"(act\s+as|you\s+are|pretend\s+to\s+be)\s*(a\s+)?(doctor|physician|admin|root|system)", re.IGNORECASE),
]

# 人工审核绕过尝试
_HUMAN_REVIEW_BYPASS_PATTERNS = [
    re.compile(r"(不需要|无需|不必|跳过|取消|关闭)\s*(人工|医生|专业)\s*(审核|复核|检查|确认)", re.IGNORECASE),
    re.compile(r"(直接|自动|自行)\s*(通过|确认|批准|完成)\s*(审核|检查|流程)", re.IGNORECASE),
    re.compile(r"(bypass|skip|disable|skip)\s*(human|manual)\s*(review|check|verification)", re.IGNORECASE),
]

# ============================================================
# 敏感信息检测模式
# ============================================================

# 中国大陆手机号（11位，1开头）
_PHONE_PATTERN = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")

# 身份证号码（18位，最后一位可以是X）
_ID_NUMBER_PATTERN = re.compile(r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")

# 电子邮箱
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# 银行卡号（16-19位数字）
_BANK_CARD_PATTERN = re.compile(r"(?<!\d)[1-9]\d{15,18}(?!\d)")

# 脱敏替换文本
_REDACTED_PHONE = "[REDACTED_PHONE]"
_REDACTED_ID = "[REDACTED_ID]"
_REDACTED_EMAIL = "[REDACTED_EMAIL]"
_REDACTED_BANK = "[REDACTED_BANK]"


@dataclass
class InputGuardResult:
    """输入安全检测结果"""
    flags: List[str] = field(default_factory=list)
    sanitized_text: str = ""
    is_safe: bool = True
    needs_human_review: bool = False
    is_blocked: bool = False


def detect_prompt_injection(text: str) -> List[str]:
    """
    检测提示词攻击

    Args:
        text: 待检测文本

    Returns:
        命中的安全标志列表
    """
    flags: List[str] = []

    # 中文提示词注入
    for pattern in _CN_INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append("prompt_injection_detected")
            break

    # 英文提示词注入
    for pattern in _EN_INJECTION_PATTERNS:
        if pattern.search(text):
            if "prompt_injection_detected" not in flags:
                flags.append("prompt_injection_detected")
            break

    # 系统提示词提取
    for pattern in _SYSTEM_PROMPT_EXTRACTION_PATTERNS:
        if pattern.search(text):
            flags.append("system_prompt_extraction_detected")
            break

    # 越权角色指令
    for pattern in _PRIVILEGE_ESCALATION_PATTERNS:
        if pattern.search(text):
            flags.append("privilege_escalation_detected")
            break

    # 人工审核绕过
    for pattern in _HUMAN_REVIEW_BYPASS_PATTERNS:
        if pattern.search(text):
            flags.append("human_review_bypass_detected")
            break

    return flags


def detect_sensitive_info(text: str) -> tuple[List[str], str]:
    """
    检测并脱敏敏感信息

    Args:
        text: 待检测文本

    Returns:
        (安全标志列表, 脱敏后文本)
    """
    flags: List[str] = []
    sanitized = text

    # 手机号
    if _PHONE_PATTERN.search(text):
        flags.append("phone_number_detected")
        sanitized = _PHONE_PATTERN.sub(_REDACTED_PHONE, sanitized)

    # 身份证号
    if _ID_NUMBER_PATTERN.search(text):
        flags.append("id_number_detected")
        sanitized = _ID_NUMBER_PATTERN.sub(_REDACTED_ID, sanitized)

    # 电子邮箱
    if _EMAIL_PATTERN.search(text):
        flags.append("email_detected")
        sanitized = _EMAIL_PATTERN.sub(_REDACTED_EMAIL, sanitized)

    # 银行卡号（仅在明确上下文中检测，避免误伤普通数字）
    if _BANK_CARD_PATTERN.search(text):
        flags.append("bank_card_detected")
        sanitized = _BANK_CARD_PATTERN.sub(_REDACTED_BANK, sanitized)

    if flags:
        flags.insert(0, "sensitive_data_detected")

    return flags, sanitized


def check_input_safety(text: str) -> InputGuardResult:
    """
    执行完整的输入安全检测

    Args:
        text: 待检测文本

    Returns:
        InputGuardResult
    """
    result = InputGuardResult()
    result.sanitized_text = text

    # 1. 提示词攻击检测
    injection_flags = detect_prompt_injection(text)
    result.flags.extend(injection_flags)

    # 2. 敏感信息检测与脱敏
    pii_flags, sanitized = detect_sensitive_info(text)
    result.flags.extend(pii_flags)
    result.sanitized_text = sanitized

    # 3. 判断安全状态
    injection_flags_set = {
        "prompt_injection_detected",
        "system_prompt_extraction_detected",
        "privilege_escalation_detected",
        "human_review_bypass_detected",
    }

    if injection_flags_set & set(result.flags):
        result.is_blocked = True
        result.needs_human_review = True
        result.is_safe = False

    if pii_flags:
        result.needs_human_review = True
        if not result.is_blocked:
            result.is_safe = False

    # 日志中不记录原始文本
    if result.flags:
        logger.warning(
            "输入安全检测命中。flags=%s",
            result.flags,
        )

    return result
