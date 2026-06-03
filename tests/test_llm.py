"""
测试 LLM 层：模型工厂、环境分层、Mock 模式、降级链
"""
import os
import pytest


class TestEnvLayers:
    """环境分层：test/dev/prod 行为不同"""

    def test_test_env_uses_mock(self):
        """test 环境应该用 Mock 模型，不调 API"""
        os.environ["APP_ENV"] = "test"
        # 强制重载 config 以读取新环境变量
        import importlib
        import llm.config
        import llm.factory
        importlib.reload(llm.config)
        importlib.reload(llm.factory)
        from llm.factory import create_model, get_model_info

        info = get_model_info()
        assert info["mode"] == "mock"

        model = create_model()
        resp = model.invoke("test")
        assert len(resp.content) > 0

    def test_env_config_exists(self):
        """三种环境配置都已定义"""
        from llm.config import ENV_CONFIG
        assert "test" in ENV_CONFIG
        assert "dev" in ENV_CONFIG
        assert "prod" in ENV_CONFIG
        # 每层都有关键字段
        for env in ENV_CONFIG.values():
            assert "use_mock" in env
            assert "retries" in env
            assert "timeout" in env
        # prod 重试次数最多
        assert ENV_CONFIG["prod"]["retries"] >= ENV_CONFIG["dev"]["retries"]

    def test_registry_has_providers(self):
        """模型注册表至少包含 deepseek 和 openai"""
        from llm.config import MODEL_REGISTRY
        assert "deepseek" in MODEL_REGISTRY
        assert "openai" in MODEL_REGISTRY
        # 每个提供商有必需字段
        for p in MODEL_REGISTRY.values():
            assert "model" in p
            assert "base_url" in p


class TestMockModel:
    """Mock 模型：不花钱验证逻辑"""

    def test_mock_returns_content(self, mock_model):
        """Mock 模型应该返回预设文本"""
        resp = mock_model.invoke("任意输入")
        assert resp.content
        assert len(resp.content) > 10

    def test_mock_context_aware(self, mock_model):
        """Mock 模型根据输入内容返回不同预设"""
        resp_budget = mock_model.invoke("计算预算")
        assert "预算" in resp_budget.content or "费用" in resp_budget.content

    def test_mock_no_api_call(self, mock_model):
        """Mock 模型元数据标识 mock"""
        resp = mock_model.invoke("test")
        assert resp.response_metadata.get("mock") is True


class TestFactory:
    """模型工厂：create_model() 的正确性"""

    def test_create_model_returns_chat_model(self):
        """create_model() 返回可调用的模型"""
        os.environ["APP_ENV"] = "test"
        from llm.factory import create_model

        model = create_model()
        resp = model.invoke("hello")
        assert resp.content

    def test_invalid_provider_raises(self):
        """不存在的提供商应该报错"""
        from llm.factory import _create_one
        with pytest.raises(ValueError, match="未知提供商"):
            _create_one("nonexistent")

    def test_get_model_info(self):
        """模型信息应该包含环境和成本"""
        os.environ["APP_ENV"] = "test"
        from llm.factory import get_model_info

        info = get_model_info()
        assert "env" in info
        assert info["cost"] == "¥0"
