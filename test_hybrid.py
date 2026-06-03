"""
混合搜索测试：本地 RAG → 联网搜索 Fallback → 自动入库
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from rag.knowledge_store import TravelKnowledgeBase

kb = TravelKnowledgeBase()
kb.build()

print("=" * 60)
print("测试1：查西安（本地有文档 → 应该秒回，不联网）")
print("=" * 60)
docs, from_web = kb.hybrid_search("西安有什么好吃的", k=3)
print(f"来源: {'联网' if from_web else '本地'} | 结果: {len(docs)} 条")
for d in docs:
    print(f"  - {d.page_content[:80]}...")

print("\n" + "=" * 60)
print("测试2：查巴厘岛（本地无文档 → 应该触发联网搜索 → 自动入库）")
print("=" * 60)
docs2, from_web2 = kb.hybrid_search("巴厘岛 旅游攻略 景点 美食", k=3)
print(f"来源: {'联网' if from_web2 else '本地'} | 结果: {len(docs2)} 条")
for d in docs2:
    print(f"  - {d.page_content[:120]}...")

print("\n" + "=" * 60)
print("测试3：再次查巴厘岛（应该走本地了，因为上次搜完已入库）")
print("=" * 60)
docs3, from_web3 = kb.hybrid_search("巴厘岛有什么好玩的", k=3)
print(f"来源: {'联网' if from_web3 else '本地'} | 结果: {len(docs3)} 条")
for d in docs3:
    print(f"  - {d.page_content[:120]}...")
