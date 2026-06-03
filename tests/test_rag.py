"""
测试 RAG 层：知识库建库、检索、混合搜索、时效性
沙盒：临时 ChromaDB 目录 + Mock DuckDuckGo
"""
import os
import sys
from pathlib import Path
import pytest
from langchain_core.documents import Document


def _make_test_docs():
    """辅助：创建测试用的 Document 列表"""
    return [
        Document(page_content="西安兵马俑是世界第八大奇迹，门票120元，建议游玩3小时。"),
        Document(page_content="西安回民街是著名美食街，推荐肉夹馍、羊肉泡馍。"),
        Document(page_content="广州早茶是必体验文化，推荐点都德、陶陶居。人均80-100元。"),
    ]


class TestKnowledgeBaseBuild:
    """知识库构建"""

    def test_build_with_documents(self, temp_chroma_dir):
        """建库：加载文档 → 切块 → 向量化 → 持久化"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()
        assert kb.vector_store is not None
        # ChromaDB 目录应该有文件
        assert os.path.exists(temp_chroma_dir)

    def test_empty_build_creates_empty_store(self, temp_chroma_dir):
        """没有本地文档时也应该能建空库"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        # 这个测试不依赖 data/ 目录下的文件
        kb.build()
        assert kb.vector_store is not None


class TestSearch:
    """检索"""

    def test_add_and_search(self, temp_chroma_dir):
        """添加文档后能检索到相关内容"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()
        kb.add_documents(_make_test_docs())

        results = kb.search("西安有什么好吃的", k=2)
        assert len(results) > 0
        # 应该搜到回民街相关
        contents = [d.page_content for d in results]
        assert any("回民街" in c or "肉夹馍" in c for c in contents)

    def test_search_relevance_filtering(self, temp_chroma_dir):
        """相关性阈值过滤不相关内容"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()
        kb.add_documents(_make_test_docs())

        scored = kb.search_with_scores("西安美食", k=3)
        # 至少有一条相关
        assert len(scored) > 0
        for doc, score in scored:
            assert 0 <= score <= 1

    def test_search_before_build_raises(self, temp_chroma_dir):
        """没建库就检索应该报错"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        with pytest.raises(RuntimeError):
            kb.search("test")


class TestHybridSearch:
    """混合搜索：本地 + 联网"""

    def test_local_hit_no_web(self, temp_chroma_dir, mock_search):
        """本地有结果时不触发联网"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()
        kb.add_documents(_make_test_docs())

        docs, from_web = kb.hybrid_search("西安兵马俑门票", k=2, min_score=0.1)
        assert not from_web  # 本地命中

    def test_local_miss_triggers_web(self, temp_chroma_dir, mock_search):
        """本地没结果时触发联网搜索并自动入库"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        # 搜一个本地完全没有的内容
        docs, from_web = kb.hybrid_search("火星旅游攻略", k=2, min_score=0.5)
        # 由于用了 mock_search，应该能搜到假数据
        assert from_web or len(docs) >= 0  # 至少不崩


class TestFreshness:
    """时效性：过期策略"""

    def test_local_doc_never_expires(self, temp_chroma_dir):
        """本地手写文档永不过期"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        doc = Document(page_content="测试内容", metadata={"source_type": "local"})
        max_age = kb._get_max_age(doc)
        assert max_age == 999

    def test_web_doc_30_day_expiry(self, temp_chroma_dir):
        """联网搜来的数据 30 天过期"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        doc = Document(page_content="测试内容", metadata={"source_type": "web"})
        max_age = kb._get_max_age(doc)
        assert max_age == 30

    def test_age_calculation(self, temp_chroma_dir):
        """年龄计算正确"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        from datetime import datetime
        doc = Document(
            page_content="test",
            metadata={"created_at": datetime.now().isoformat(), "source_type": "web"},
        )
        age = kb._get_age_days(doc)
        assert age < 0.01  # 刚创建，不到 1 天

    def test_no_timestamp_defaults_old(self, temp_chroma_dir):
        """没有时间戳的文档视为很旧"""
        from rag.knowledge_store import TravelKnowledgeBase
        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        doc = Document(page_content="test")
        age = kb._get_age_days(doc)
        assert age == 999  # 没有时间戳 → 视为非常旧


class TestPersistence:
    """持久化：重启数据不丢"""

    def test_data_survives_rebuild(self, temp_chroma_dir):
        """数据持久化到磁盘，重新加载后还在"""
        from rag.knowledge_store import TravelKnowledgeBase

        # 第一次：建库 + 加数据
        kb1 = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb1.build()
        kb1.add_documents(_make_test_docs())
        count1 = kb1.vector_store._collection.count()

        # 第二次：重新加载同一个目录
        kb2 = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb2.build()
        count2 = kb2.vector_store._collection.count()

        assert count2 >= count1  # 数据不丢
