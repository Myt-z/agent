"""
Mock 模型 —— 开发/测试时不调用真实 API，不花钱

设置 LLM_DEV_MODE=true 启用。
返回预设回复并模拟 tool calling，用于验证 Agent 调度逻辑。
"""

from langchain_core.messages import AIMessage

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
    """模拟 ChatModel，返回预设回复并触发 tool calling 流程"""

    def __init__(self):
        self._call_count = 0

    def invoke(self, messages, **kwargs):
        self._call_count += 1
        content = str(messages)

        # 第一轮：按 system_prompt 中的 SOP 顺序调用工具
        if "第1步" in content and "plan_itinerary" in content and self._call_count <= 2:
            return AIMessage(
                content="",
                tool_calls=[{
                    "id": "mock_call_1",
                    "name": "plan_itinerary",
                    "args": {"city": "西安", "days": 3, "preferences": "综合体验"},
                }],
                response_metadata={"mock": True},
            )

        # 判断当前是哪个工具调用的返回，决定下一个工具
        tool_results = self._extract_tool_results(messages)
        if any("行程安排" in str(r) for r in tool_results) and "第2步" in content:
            return AIMessage(
                content="",
                tool_calls=[{
                    "id": "mock_call_2",
                    "name": "analyze_budget",
                    "args": {"itinerary_text": MOCK_RESPONSES["itinerary"], "total_budget": 3000},
                }],
                response_metadata={"mock": True},
            )

        if any("预算" in str(r) for r in tool_results) and "第3步" in content:
            return AIMessage(
                content="",
                tool_calls=[{
                    "id": "mock_call_3",
                    "name": "explain_culture",
                    "args": {"city": "西安", "topics": "历史文化,风俗礼仪"},
                }],
                response_metadata={"mock": True},
            )

        # 最终汇总回复
        return AIMessage(
            content=f"# 西安 3日游完整计划\n\n{MOCK_RESPONSES['itinerary']}\n\n{MOCK_RESPONSES['budget']}\n\n{MOCK_RESPONSES['culture']}\n\n（Mock 模式 —— 已验证 Agent 调度逻辑全部正常）",
            response_metadata={"mock": True, "model": "mock-model"},
        )

    def _extract_tool_results(self, messages):
        results = []
        for m in messages if isinstance(messages, list) else messages.get("messages", []):
            if hasattr(m, "type") and m.type == "tool":
                results.append(getattr(m, "content", ""))
        return results

    def bind_tools(self, tools):
        return self

    def __str__(self):
        return "MockChatModel (dev mode, tool-calling simulation enabled)"
