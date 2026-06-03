"""
测试共享夹具 —— 沙盒环境

所有外部依赖被关进笼子：
  - LLM    → Mock 模型（不调 API）
  - ChromaDB → 临时目录（跑完自动销毁）
  - DuckDuckGo → 注入假数据（不联网）

用法：pytest tests/ -v   # 3 秒跑完，¥0
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# 强制 test 环境
os.environ["APP_ENV"] = "test"

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def sandbox_env():
    """每个测试自动进入沙盒环境"""
    # 保存原始环境
    original = {k: v for k, v in os.environ.items()}
    os.environ["APP_ENV"] = "test"
    yield
    # 恢复
    os.environ.clear()
    os.environ.update(original)


@pytest.fixture
def mock_model():
    """Mock 模型 —— 不调 API，返回预设文本"""
    from llm.mock import MockChatModel
    return MockChatModel()


@pytest.fixture
def temp_chroma_dir():
    """临时 ChromaDB 目录 —— 跑完自动删除"""
    tmp = tempfile.mkdtemp(prefix="chroma_test_")
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def mock_search():
    """Mock DuckDuckGo —— 注入假搜索结果，不联网"""
    fake_results = [
        {
            "title": "测试结果1",
            "body": "这是模拟的搜索结果内容，用于沙盒测试。包含旅游攻略信息。",
            "href": "https://example.com/test1",
        },
        {
            "title": "测试结果2",
            "body": "第二条模拟搜索结果，验证搜索格式化和入库逻辑。",
            "href": "https://example.com/test2",
        },
    ]
    with patch("tools.search_tools.web_search", return_value=fake_results):
        yield fake_results
