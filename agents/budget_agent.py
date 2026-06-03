"""
预算计算 Agent —— 负责旅行费用分析和预算规划

核心技能：
  1. calculate_budget：计算总预算
  2. get_reference_price：查询市场参考价

设计思路：
  这个 Agent 不查 RAG，只用工具函数。
  展示的是 Agent = model + @tool 工具 的最简模式。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from tools.travel_tools import calculate_budget, get_reference_price


class BudgetAgent:
    """
    旅行预算专家 Agent。

    职责：根据行程方案估算费用，给出省钱建议。
    """

    def __init__(self):
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
        )

        self.tools = [calculate_budget, get_reference_price]

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt="""你是一位专业的旅行预算分析师，帮用户精打细算。

你的工作方式：
1. 收到行程后，先用 get_reference_price 查询各项费用的市场参考价
2. 再用 calculate_budget 工具计算总预算
3. 给出省钱建议（如：坐地铁不打车、吃小吃不吃大餐、提前订票等）

输出格式：
- 各项费用明细（交通、住宿、餐饮、门票、其他）
- 总计
- 如果用户给了预算上限，判断是否超支
- 3 条省钱建议
""",
        )

    def analyze(self, itinerary_text: str, total_budget: float = 0) -> str:
        """分析行程预算"""
        budget_hint = f"，用户总预算上限 {total_budget} 元" if total_budget > 0 else ""
        prompt = f"请根据以下行程方案，估算各项费用{budget_hint}：\n\n{itinerary_text}"
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return result["messages"][-1].content
