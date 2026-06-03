"""
模型配置中心 —— 一处管理，全局生效

环境分层：
  APP_ENV=test   → Mock 模型，不花钱，调 Agent 逻辑用
  APP_ENV=dev    → 真实 API，打印调试日志
  APP_ENV=prod   → 真实 API，只打印错误日志，完整降级链

换模型：
  LLM_PROVIDER=deepseek  → DeepSeek
  LLM_PROVIDER=openai    → OpenAI
  LLM_MODEL=gpt-4o-mini  → 换模型名（不设就用默认）
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ===== 环境 =====
APP_ENV = os.getenv("APP_ENV", "dev")

ENV_CONFIG = {
    "test": {
        "use_mock": True,
        "log_level": logging.DEBUG,
        "retries": 0,
        "timeout": 10,
    },
    "dev": {
        "use_mock": False,
        "log_level": logging.DEBUG,
        "retries": 1,
        "timeout": 60,
    },
    "prod": {
        "use_mock": False,
        "log_level": logging.ERROR,
        "retries": 3,
        "timeout": 90,
    },
}
CURRENT_ENV = ENV_CONFIG.get(APP_ENV, ENV_CONFIG["dev"])

# ===== 模型注册表 =====
MODEL_REGISTRY = {
    "deepseek": {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    },
    "openai": {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    },
    "openrouter": {
        "model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4"),
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": "https://openrouter.ai/api/v1",
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    },
}

# ===== 降级链 =====
FALLBACK_CHAIN = os.getenv("LLM_FALLBACK_CHAIN", "deepseek,openai").split(",")

# ===== 便捷查询 =====
DEV_MODE = CURRENT_ENV["use_mock"]
MAX_RETRIES = CURRENT_ENV["retries"]
REQUEST_TIMEOUT = CURRENT_ENV["timeout"]


def get_current_provider() -> str:
    return FALLBACK_CHAIN[0].strip()


def get_current_model() -> str:
    return MODEL_REGISTRY.get(get_current_provider(), {}).get("model", "unknown")
