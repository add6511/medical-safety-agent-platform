"""
日志配置模块
配置结构化日志，确保敏感信息（API密钥、密码、患者数据）不会被输出
"""

import logging
import sys
from app.core.config import settings


class SensitiveFilter(logging.Filter):
    """
    日志过滤器：屏蔽可能包含敏感信息的日志内容
    包括 API Key、密码、患者数据关键词等
    """

    SENSITIVE_KEYWORDS = [
        "api_key", "apikey", "api-key",
        "password", "passwd", "pwd",
        "secret", "token", "authorization",
        "患者", "姓名", "身份证", "手机号",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """检查日志消息中是否包含敏感关键词"""
        message = record.getMessage().lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in message:
                record.msg = "[敏感信息已屏蔽]"
                record.args = ()
                break
        return True


def setup_logging() -> None:
    """配置应用日志"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # 设置日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # 添加敏感信息过滤器
    handler.addFilter(SensitiveFilter())

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # 降低第三方库的日志级别，避免过多输出
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
