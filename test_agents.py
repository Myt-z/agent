"""
Phase 3 测试：三个 Agent 独立运行
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("测试 1: 行程规划 Agent")
print("=" * 60)
from agents.itinerary_agent import ItineraryAgent

itinerary = ItineraryAgent()
result = itinerary.plan(city="西安", days=3, preferences="历史文化+美食")
print(result[:500])
print("...(行程规划 OK)")

print("\n" + "=" * 60)
print("测试 2: 预算计算 Agent")
print("=" * 60)
from agents.budget_agent import BudgetAgent

budget = BudgetAgent()
result = budget.analyze(
    itinerary_text="西安3日游：第1天大雁塔+回民街，第2天兵马俑+华清池，第3天城墙+钟楼",
    total_budget=3000
)
print(result[:500])
print("...(预算分析 OK)")

print("\n" + "=" * 60)
print("测试 3: 文化讲解 Agent")
print("=" * 60)
from agents.culture_agent import CultureAgent

culture = CultureAgent()
result = culture.explain(city="西安")
print(result[:500])
print("...(文化讲解 OK)")
