"""
行程规划 Agent —— 负责制定每日行程方案

核心技能：
  1. RAG 检索：从旅行攻略知识库里搜相关信息
  2. MCP 天气：查询目的地天气（影响行程安排）

设计思路：
  把 RAG retriever 包装成 tool → Agent 就能"查资料"了
  把 MCP weather 包装成 tool → Agent 就能"查天气"了
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

from rag.knowledge_store import TravelKnowledgeBase

# 全局知识库（单例，线程安全）
_kb = None
_lock = threading.Lock()


def get_knowledge_base():
    global _kb
    if _kb is None:
        with _lock:
            if _kb is None:
                _kb = TravelKnowledgeBase()
                _kb.build()
    return _kb


def _search_travel_guide(query: str) -> str:
    """从知识库检索旅行攻略（优先本地，无结果则联网搜索）"""
    kb = get_knowledge_base()
    docs, from_web = kb.hybrid_search(query, k=3)
    if not docs:
        return "本地和网络均未找到相关信息，请尝试换个关键词搜索"

    source_tag = " [来源：网络实时搜索]" if from_web else " [来源：本地知识库]"
    return "\n\n".join(
        f"[资料{i+1}]{source_tag}\n{d.page_content}"
        for i, d in enumerate(docs)
    )


class ItineraryAgent:
    """
    行程规划专家 Agent。

    职责：根据目的地、天数、偏好，规划每日行程。
    能查攻略（RAG）+ 查天气（MCP）。
    """

    def __init__(self):
        # 1. 大模型
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL"),
        )

        # 2. RAG 检索工具
        @tool
        def search_guide(query: str) -> str:
            """
            搜索旅行攻略知识库。
            当你需要了解目的地的景点、美食、交通、注意事项时使用此工具。
            参数 query: 搜索关键词，如 '西安景点推荐'、'西安美食攻略'
            """
            return _search_travel_guide(query)

        # 3. 行程规划专用工具
        @tool
        def get_day_plan(day_number: int, city: str, focus: str) -> str:
            """
            为指定天数制定当日行程建议格式。
            参数 day_number: 第几天（1/2/3...）
            参数 city: 城市名
            参数 focus: 当日的重点主题，如 历史文化、美食、自然风光
            """
            return f"请为{city}第{day_number}天制定以「{focus}」为主题的行程"

        self.tools = [search_guide, get_day_plan]

        # 4. 创建 Agent
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt="""你是一位资深的旅行行程规划师，专门为用户制定详细、可行的旅行计划。

你的工作方式：
1. 先用 search_guide 工具搜索目的地的景点、美食、交通信息
2. 再用 get_day_plan 工具为每一天制定主题行程
3. 综合所有信息，输出一份完整的 N 日游行程方案

输出格式要求：
- 每天一个段落，格式为「第X天：主题名称 → 上午...→ 下午...→ 晚上...」
- 推荐 2-3 个必吃美食
- 标注交通建议（地铁哪号线、打车约多少钱）
- 如果有天气信息，给出穿衣建议
""",
        )

    def plan(self, city: str, days: int, preferences: str = "综合体验") -> str:
        """制定行程方案"""
        prompt = f"请为「{city}」制定一份 {days} 天的旅行行程，偏好：「{preferences}」。请先搜索攻略再规划。"
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return result["messages"][-1].content
