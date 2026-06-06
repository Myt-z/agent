"""
推荐 Agent —— 用户不知道去哪时，根据预算和偏好推荐城市

输入：预算 + 天数 + 偏好 + 当前季节
输出：推荐城市 + 理由 + 预估费用

使用场景：用户在 city 输入框留空或输入"推荐"
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from langchain.agents import create_agent
from langchain_core.tools import tool
from llm.factory import create_model

from rag.knowledge_store import TravelKnowledgeBase
import threading

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


@tool
def list_available_cities() -> str:
    """
    列出本地知识库中有攻略文档的城市。
    这些城市的旅行计划会最准确。
    """
    kb = _get_kb()
    import glob
    files = list(Path(kb.data_dir).glob("*.txt"))
    cities = []
    for f in files:
        name = f.stem.replace("_guide", "").replace("-guide", "")
        cities.append(name)
    # 也列出管道入库的城市
    try:
        from db.database import get_popular_cities
        db_cities = [p["city"] for p in get_popular_cities(20)]
        cities = sorted(set(cities + db_cities))
    except Exception:
        pass
    return "本地有详细攻略的城市：" + "、".join(cities)


@tool
def search_city_info(city: str) -> str:
    """
    搜索某个城市的基本信息（景点、特色、适合季节）。
    参数 city: 城市名
    """
    kb = _get_kb()
    docs, _ = kb.hybrid_search(f"{city} 旅游 特色 季节", k=3)
    if not docs:
        return f"暂无 {city} 的详细资料"
    return "\n".join(d.page_content[:200] for d in docs)


class RecommendAgent:
    """
    目的地推荐专家。

    输入预算、天数、偏好 → 推荐最合适的城市。
    """

    def __init__(self):
        self.model = create_model()

        self.agent = create_agent(
            model=self.model,
            tools=[list_available_cities, search_city_info],
            system_prompt="""你是一个旅行目的地推荐专家。

你的工作方式：
1. 先用 list_available_cities 查看本地有哪些城市的攻略
2. 根据用户给出的预算、天数、偏好，从这些城市里推荐最合适的 1-3 个
3. 用 search_city_info 查一下推荐城市的特色
4. 综合考虑这些因素：
   - 预算是否匹配当地消费水平
   - 季节是否适合（如夏天避开火炉城市，冬天推荐温暖城市）
   - 偏好是否匹配城市特色（历史文化→古都，美食→广州成都，自然风光→有山有水的城市）
   - 天数是否够玩主要景点
5. 给出推荐结果，格式：
   - 推荐城市 + 推荐理由（3-5 句话）
   - 预估总费用
   - 如果用户预算不够，诚实说出来并推荐更便宜的目的地

当前季节参考：{season}
""".format(season=_guess_season()),
        )

    def recommend(self, budget: float, days: int, preferences: str = "综合体验") -> str:
        """智能推荐目的地"""
        prompt = (
            f"用户需求：预算 {budget} 元，{days} 天，偏好「{preferences}」。"
            f"请先查看本地有哪些城市的攻略，然后推荐最合适的目的地。"
        )
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        return result["messages"][-1].content


def _guess_season() -> str:
    """根据当前月份猜季节"""
    month = datetime.now().month
    if 3 <= month <= 5:
        return "春季"
    elif 6 <= month <= 8:
        return "夏季"
    elif 9 <= month <= 11:
        return "秋季"
    else:
        return "冬季"
