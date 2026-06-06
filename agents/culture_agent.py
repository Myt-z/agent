"""
文化讲解 Agent —— 负责目的地文化背景介绍

核心技能：
  1. RAG 检索：从文化知识库里搜相关信息
  2. 纯知识：博物馆背景、历史故事、当地风俗

设计思路：
  这个 Agent 只做"讲解"，不做规划、不算钱。
  展示的是如何给 Agent 绑定专属的 RAG 知识库。
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from langchain.agents import create_agent
from langchain_core.tools import tool
from llm.factory import create_model

from rag.knowledge_store import TravelKnowledgeBase

_kb = None
_lock = threading.Lock()


def _get_kb():
    global _kb
    if _kb is None:
        with _lock:
            if _kb is None:
                _kb = TravelKnowledgeBase()
                _kb.build()
    return _kb


def _search_culture(query: str) -> str:
    """从文化知识库检索（优先本地，无结果则联网搜索）"""
    docs, from_web = _get_kb().hybrid_search(query, k=3)
    if not docs:
        return "本地和网络均未找到相关文化资料，请尝试换个关键词搜索"

    source_tag = " [来源：网络实时搜索]" if from_web else " [来源：本地知识库]"
    return "\n\n".join(
        f"[资料{i+1}]{source_tag}\n{d.page_content}"
        for i, d in enumerate(docs)
    )


class CultureAgent:
    """
    文化讲解专家 Agent。

    职责：讲解目的地的历史文化、风俗礼仪、旅行注意事项。
    """

    def __init__(self):
        self.model = create_model()

        @tool
        def search_culture_knowledge(query: str) -> str:
            """
            搜索旅行文化知识库。
            当你需要了解当地历史、文化背景、风俗禁忌、参观礼仪时使用此工具。
            参数 query: 搜索关键词，如 '西安历史文化'、'寺庙参观礼仪'
            """
            return _search_culture(query)

        self.tools = [search_culture_knowledge]

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt="""你是一位博学的旅行文化专家，专门为用户介绍目的地的文化背景。

你的工作方式：
1. 收到目的地后，用 search_culture_knowledge 搜索相关文化资料
2. 讲解内容包括：
   - 当地的历史文化亮点（不需要长篇大论，挑最重要的 2-3 个讲）
   - 风俗禁忌和参观礼仪（特别是寺庙、少数民族地区）
   - 2-3 个有趣的冷知识

输出格式：
- 用「历史文化」「风俗礼仪」「趣味冷知识」三个板块组织
- 每个板块不超过 5 句话
- 语言生动有趣，像在跟朋友聊天
""",
        )

    def explain(self, city: str, topics: str = "历史文化,风俗礼仪") -> str:
        """讲解目的地文化背景"""
        prompt = f"请为「{city}」讲解旅行文化知识，重点关注：{topics}。请先搜索知识库再回答。"
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return result["messages"][-1].content
