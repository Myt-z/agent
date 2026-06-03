"""
结构化日志 —— 替代所有 print()

功能：
  - 控制台输出（开发时看）
  - 文件写入 + 按天切割（生产时查）
  - 日志目录：logs/
  - 保留最近 7 天

用法：
  from utils.logging import get_logger
  logger = get_logger(__name__)
  logger.info("模型已创建", extra={"provider": "deepseek", "model": "deepseek-chat"})
"""
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_initialized = False


def setup_logging():
    """初始化日志系统（全局调一次）"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    LOG_DIR.mkdir(exist_ok=True)

    # 根 logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # 格式：时间 | 级别 | 模块 | 消息
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if os.getenv("APP_ENV") == "dev" else logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件 handler —— 按天切割，保留 7 天
    file_handler = TimedRotatingFileHandler(
        filename=LOG_DIR / "travel_planner.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # 错误日志单独一份
    error_handler = TimedRotatingFileHandler(
        filename=LOG_DIR / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    # 抑制第三方库的噪音
    for noisy in ["httpx", "openai", "urllib3", "chromadb", "sentence_transformers"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("travel-planner").info(f"日志系统就绪 | 环境: {os.getenv('APP_ENV', 'dev')} | 级别: {LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """获取模块级 logger"""
    setup_logging()  # 幂等
    return logging.getLogger(name)
