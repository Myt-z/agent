"""
主控调度 Agent —— Agent-Team 的"项目经理"

核心模式：把每个子 Agent 包装成一个 @tool → 主控 Agent 决定何时调用谁

数据流：
  用户需求 → 主控 Agent
    → 调 itinerary_tool → 拿到行程方案
    → 调 budget_tool → 拿到预算分析
    → 调 culture_tool → 拿到文化讲解
    → 汇总输出完整旅行计划
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain.agents import create_agent
from langchain_core.tools import tool
from llm.factory import create_model
from utils.logging import get_logger

logger = get_logger("agents.coordinator")

from agents.itinerary_agent import ItineraryAgent
from agents.budget_agent import BudgetAgent
from agents.culture_agent import CultureAgent


class TravelCoordinator:
    """
    旅行规划总调度。

    内部持有 3 个专业 Agent：
      - 行程规划师（查攻略 + 排行程）
      - 预算分析师（算费用 + 省钱的建议）
      - 文化讲解员（讲历史 + 说风俗）

    每个 Agent 被包装成 tool，主控 Agent 按 system_prompt
    里定义的 SOP 顺序调度它们。
    """

    def __init__(self):
        # 初始化三个子 Agent（每个内部有自己的 model 和 tools）
        logger.info("初始化子 Agent")
        self.itinerary = ItineraryAgent()
        self.budget = BudgetAgent()
        self.culture = CultureAgent()

        # 把子 Agent 的方法包装成 @tool
        @tool
        def plan_itinerary(city: str, days: int, preferences: str) -> str:
            """
            调用行程规划专家，制定每日行程方案。
            参数 city: 目的地城市名，如 西安、成都
            参数 days: 游玩天数
            参数 preferences: 偏好主题，如 历史文化、美食、自然风光
            """
            logger.info(f"调度行程规划师 | city={city} days={days}")
            try:
                return self.itinerary.plan(city, days, preferences)
            except Exception as e:
                logger.error(f"行程规划师执行失败: {e}", exc_info=True)
                return "## 行程安排\n\n该模块暂时不可用，请稍后重试。建议手动搜索目的地攻略。"

        @tool
        def analyze_budget(itinerary_text: str, total_budget: float) -> str:
            """
            调用预算分析师，根据行程方案估算费用。
            参数 itinerary_text: 行程方案文本（从行程规划师那里获取）
            参数 total_budget: 用户的总预算上限（元）
            """
            logger.info(f"调度预算分析师 | budget={total_budget}")
            try:
                return self.budget.analyze(itinerary_text, total_budget)
            except Exception as e:
                logger.error(f"预算分析师执行失败: {e}", exc_info=True)
                return "## 费用预算\n\n该模块暂时不可用，请稍后重试。参考日均花费约 300-500 元/天（含住宿餐饮）。"

        @tool
        def explain_culture(city: str, topics: str) -> str:
            """
            调用文化讲解专家，介绍目的地的历史文化背景。
            参数 city: 目的地城市名
            参数 topics: 想了解的文化主题，如 历史文化,风俗礼仪,当地美食文化
            """
            logger.info(f"调度文化讲解员 | city={city}")
            try:
                return self.culture.explain(city, topics)
            except Exception as e:
                logger.error(f"文化讲解员执行失败: {e}", exc_info=True)
                return "## 文化贴士\n\n该模块暂时不可用，请稍后重试。建议查看当地旅游局的官方网站了解文化习俗。"

        # 主控模型
        self.model = create_model()

        # 主控 Agent：system_prompt 定义了 SOP（标准操作流程）
        self.agent = create_agent(
            model=self.model,
            tools=[plan_itinerary, analyze_budget, explain_culture],
            system_prompt="""你是一个旅行规划总调度员。你的工作是协调三位专家完成一份完整的旅行计划。

你必须严格按照以下流程执行（不要跳过任何步骤）：

第1步：调用 plan_itinerary 获取行程方案
第2步：拿到行程后，立即调用 analyze_budget 计算费用
第3步：调用 explain_culture 获取文化背景介绍
第4步：把以上三份结果整合，输出最终旅行计划书

最终输出格式：
---
# {城市} {天数}日游完整计划

## 一、行程安排
[行程方案内容]

## 二、费用预算
[预算分析内容]

## 三、文化贴士
[文化讲解内容]
---
""",
        )

    def plan(self, city: str, days: int, budget: float = 3000, preferences: str = "综合体验") -> str:
        """启动一次完整的旅行规划"""
        prompt = (
            f"请按流程完成以下旅行规划：\n"
            f"- 目的地：{city}\n"
            f"- 天数：{days} 天\n"
            f"- 总预算：{budget} 元\n"
            f"- 偏好：{preferences}\n"
        )
        logger.info(f"开始规划 | city={city} days={days} budget={budget} preferences={preferences}")
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return result["messages"][-1].content
