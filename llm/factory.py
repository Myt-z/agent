"""
模型工厂 —— 业务代码调 create_model()，不关心底层

环境感知：
  test  → Mock 模型（不调 API）
  dev   → 真实 API + 调试日志
  prod  → 真实 API + 错误日志 + 完整降级链
"""
import logging
from langchain_openai import ChatOpenAI
from llm.config import (
    MODEL_REGISTRY,
    FALLBACK_CHAIN,
    DEV_MODE,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    APP_ENV,
    CURRENT_ENV,
)

logger = logging.getLogger("travel-planner.llm")
logger.setLevel(CURRENT_ENV["log_level"])


def create_model(provider: str = None, fallback: bool = True):
    """
    创建 LLM 模型实例。自动根据 APP_ENV 选择行为。

    test:  返回 Mock 模型，不调 API
    dev:   真实 API，日志详细，重试 1 次
    prod:  真实 API，只记错误，重试 3 次，自动降级
    """
    if DEV_MODE:
        from llm.mock import MockChatModel
        logger.debug("[LLM] test 模式，使用 Mock 模型")
        return MockChatModel()

    if provider:
        return _create_one(provider)

    if not fallback:
        return _create_one(FALLBACK_CHAIN[0].strip())

    # 降级链
    last_error = None
    for p in FALLBACK_CHAIN:
        p = p.strip()
        try:
            model = _create_one(p)
            logger.info(f"[LLM] 连接 {p} ({MODEL_REGISTRY[p]['model']}) [env={APP_ENV}]")
            return model
        except Exception as e:
            last_error = e
            logger.warning(f"[LLM] {p} 不可用: {e}，尝试下一个...")

    raise RuntimeError(
        f"所有模型提供商不可用 (env={APP_ENV}, chain={FALLBACK_CHAIN})。"
        f"最后错误: {last_error}"
    )


def _create_one(provider: str):
    """创建单个模型实例"""
    provider = provider.strip()
    if provider not in MODEL_REGISTRY:
        raise ValueError(f"未知提供商 '{provider}'，已知: {list(MODEL_REGISTRY.keys())}")

    cfg = MODEL_REGISTRY[provider]
    if not cfg["api_key"]:
        raise ValueError(f"{provider} API Key 未设置。在 .env 中配置 {provider.upper()}_API_KEY")

    return ChatOpenAI(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["base_url"],
        temperature=cfg["temperature"],
        max_retries=MAX_RETRIES,
        timeout=REQUEST_TIMEOUT,
    )


def get_model_info() -> dict:
    """当前模型信息（调试用）"""
    if DEV_MODE:
        return {"env": APP_ENV, "mode": "mock", "cost": "¥0"}
    provider = FALLBACK_CHAIN[0].strip()
    return {
        "env": APP_ENV,
        "provider": provider,
        "model": MODEL_REGISTRY.get(provider, {}).get("model", "unknown"),
        "retries": MAX_RETRIES,
        "timeout": REQUEST_TIMEOUT,
    }
