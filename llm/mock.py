"""
Mock 模型 —— 开发/测试时不调用真实 API，不花钱

设置 LLM_DEV_MODE=true 启用。
返回预设回复，用于验证 Agent 调度逻辑。
"""

MOCK_RESPONSES = {
    "itinerary": """
## 行程安排（Mock 数据）

### 第1天：文化探索
上午参观当地著名博物馆，下午游览历史街区，晚上品尝地道小吃。

### 第2天：自然风光
上午爬山/逛公园，下午乘船游湖，晚上看日落。

### 第3天：休闲购物
上午逛当地市场，下午自由活动，晚上返程。
""",
    "budget": """
## 预算分析（Mock 数据）

| 项目 | 费用 |
|------|------|
| 交通 | 500 元 |
| 住宿 | 600 元（3晚） |
| 餐饮 | 300 元 |
| 门票 | 200 元 |
| 总计 | 1600 元 |
""",
    "culture": """
## 文化贴士（Mock 数据）

当地有悠久的历史文化，建议提前了解当地风俗。
参观寺庙时注意着装得体，不要大声喧哗。
""",
    "default": "这是一个 Mock 回复，用于开发测试。设置 LLM_DEV_MODE=false 启用真实 API。",
}


class MockChatModel:
    """模拟 ChatModel，返回预设回复，不调 API"""

    def invoke(self, messages, **kwargs):
        return self._respond(messages)

    def _respond(self, messages):
        content = str(messages)
        # 根据输入内容返回不同预设
        if "行程" in content or "itinerary" in content:
            text = MOCK_RESPONSES["itinerary"]
        elif "预算" in content or "budget" in content:
            text = MOCK_RESPONSES["budget"]
        elif "文化" in content or "culture" in content:
            text = MOCK_RESPONSES["culture"]
        else:
            text = MOCK_RESPONSES["default"]

        # 返回一个类似 AIMessage 的对象
        return MockResponse(text)

    def bind_tools(self, tools):
        return self

    def __str__(self):
        return "MockChatModel (dev mode, no API calls)"


class MockResponse:
    """模拟 AIMessage"""
    def __init__(self, content):
        self.content = content
        self.tool_calls = []
        self.response_metadata = {"mock": True, "model": "mock-model"}
