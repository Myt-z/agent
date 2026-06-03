"""
Agent 工具函数 —— 用 @tool 装饰器定义

核心理解：@tool 做了两件事
  1. 把函数变成 LangChain 认识的 Tool 对象
  2. 把函数的 docstring 变成 LLM 看到的"工具说明书"

LLM 就是通过读 docstring 来决定什么时候调用这个工具的。
"""

from langchain_core.tools import tool


@tool
def calculate_budget(
    transport: float,
    hotel_per_night: float,
    days: int,
    food_per_day: float,
    other: float = 0,
) -> str:
    """
    计算旅行总预算。

    参数:
    - transport: 往返交通费（元）
    - hotel_per_night: 每晚住宿费（元）
    - days: 游玩天数
    - food_per_day: 每日餐饮预算（元）
    - other: 其他费用（门票、购物等，元）

    返回: 详细预算明细和总计
    """
    hotel_total = hotel_per_night * days
    food_total = food_per_day * days
    total = transport + hotel_total + food_total + other

    return f"""
    旅行预算明细：
    - 交通：{transport} 元
    - 住宿：{hotel_per_night} 元/晚 × {days} 晚 = {hotel_total} 元
    - 餐饮：{food_per_day} 元/天 × {days} 天 = {food_total} 元
    - 其他（门票/购物）：{other} 元
    - 总计：{total} 元
    """


@tool
def get_reference_price(item: str) -> str:
    """
    查询常见旅行消费的参考价格。

    参数:
    - item: 要查询的项目，如 经济型酒店、中档酒店、景点门票、高铁票、飞机票

    返回: 该项目的参考价格范围
    """
    prices = {
        "经济型酒店": "150-250 元/晚（如家、汉庭、7天等连锁）",
        "中档酒店": "300-500 元/晚（全季、亚朵、如家精选）",
        "高档酒店": "600-1500 元/晚（希尔顿、洲际、本地五星级）",
        "青年旅舍": "50-80 元/床位",
        "景点门票": "50-150 元/人（一般景点），兵马俑 120 元、故宫 60 元",
        "高铁票": "二等座约 0.5 元/公里，如 北京→西安 约 500 元",
        "飞机票": "提前 2 周订，经济舱 600-1500 元（国内主流航线）",
        "当地小吃": "15-40 元/份（肉夹馍 15 元、凉皮 12 元）",
        "正餐": "人均 50-100 元（普通餐厅），人均 15-30 元（快餐）",
        "市内交通": "地铁 3-8 元/次，公交 2 元/次，打车起步约 10-15 元",
    }
    result = prices.get(item, f"暂无「{item}」的参考价格。可查询的项目：{', '.join(prices.keys())}")
    return f"{item}：{result}"
