"""
RAG 知识库 —— 向量检索 + 持久化 + 时效性管理

核心改进：
  1. 持久化到磁盘（ChromaDB persist_directory）→ 重启不丢
  2. 每条文档带 created_at 时间戳 → 知道什么时候存的
  3. 检索时自动过滤过期数据 → 价格 90 天、文化 365 天
  4. 过期数据重新联网搜索 → 自动刷新
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.logging import get_logger

logger = get_logger("rag.knowledge_store")

# 简单规则：联网搜来的数据 30 天后自动刷新
# 你手写的本地文档永不过期
WEB_CACHE_DAYS = 30


class TravelKnowledgeBase:
    def __init__(self, persist_dir: str = None):
        self.data_dir = Path(__file__).parent / "data"
        self.persist_dir = persist_dir or str(Path(__file__).parent / "chroma_db")

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "，", " "],
        )

        self.vector_store = None

    def build(self):
        """加载本地 txt → 切块 → 向量化 → 持久化到磁盘"""
        all_documents = []
        txt_files = list(self.data_dir.glob("*.txt"))

        if txt_files:
            logger.info(f"找到 {len(txt_files)} 个本地文档，开始建库")
            for filepath in txt_files:
                loader = TextLoader(str(filepath), encoding="utf-8")
                docs = loader.load()
                chunks = self.text_splitter.split_documents(docs)
                # 本地文档标记为永久有效，但加上时间戳
                for chunk in chunks:
                    chunk.metadata["created_at"] = datetime.now().isoformat()
                    chunk.metadata["source_type"] = "local"
                logger.debug(f"  {filepath.name}: {len(docs)} 个文档 -> {len(chunks)} 个 chunk")
                all_documents.extend(chunks)

            logger.info(f"共 {len(all_documents)} 个 chunk，开始向量化")

            self.vector_store = Chroma.from_documents(
                documents=all_documents,
                embedding=self.embeddings,
                collection_name="travel_knowledge",
                persist_directory=self.persist_dir,
            )
        else:
            # 没有本地文档，尝试加载已有向量库
            logger.info("无本地文档，尝试加载已有向量库")
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                collection_name="travel_knowledge",
                persist_directory=self.persist_dir,
            )

        count = self.vector_store._collection.count()
        logger.info(f"知识库就绪，共 {count} 条向量 | 持久化: {self.persist_dir}")

    def add_documents(self, documents: list[Document], source: str = "web") -> int:
        """动态添加文档（联网搜索结果）并持久化"""
        if self.vector_store is None:
            raise RuntimeError("知识库还没建，先调 build()")

        now = datetime.now().isoformat()
        for doc in documents:
            doc.metadata["created_at"] = now
            doc.metadata["source_type"] = source

        chunks = self.text_splitter.split_documents(documents)
        if chunks:
            self.vector_store.add_documents(chunks)
            logger.info(f"新增 {len(chunks)} 条记录 | 来源: {source}")
        return len(chunks)

    def search(self, query: str, k: int = 3) -> list[Document]:
        if self.vector_store is None:
            raise RuntimeError("知识库还没建，先调 build()")
        return self.vector_store.similarity_search(query, k=k)

    def search_with_scores(self, query: str, k: int = 3) -> list[tuple[Document, float]]:
        if self.vector_store is None:
            raise RuntimeError("知识库还没建，先调 build()")
        return self.vector_store.similarity_search_with_relevance_scores(query, k=k)

    def hybrid_search(self, query: str, k: int = 3, min_score: float = 0.25) -> tuple[list[Document], bool]:
        """
        混合搜索 + 时效性检查。

        规则：
          1. 本地有足够新鲜结果 → 直接返回，不联网
          2. 本地有部分结果但全部过期 → 联网刷新
          3. 本地完全无结果 → 联网搜索 → 自动入库
        """
        scored = self.search_with_scores(query, k=max(k * 2, 6))
        relevant = [(doc, s) for doc, s in scored if s >= min_score]

        if relevant:
            fresh, stale = [], []
            for doc, s in relevant:
                age_days = self._get_age_days(doc)
                max_days = self._get_max_age(doc)
                if age_days <= max_days:
                    fresh.append((doc, s))
                else:
                    stale.append((doc, s))

            # 有新鲜结果就返回（哪怕不够 k 条也先用着）
            if fresh:
                return [doc for doc, _ in fresh[:k]], False

            # 全部过期 → 联网刷新
            if stale:
                oldest = min(self._get_age_days(d) for d, _ in stale)
                logger.info(f"时效检查: {len(stale)} 条已过期 ({int(oldest)}天 > {WEB_CACHE_DAYS}天)，触发刷新")

        # 联网搜索
        from tools.search_tools import web_search, results_to_documents

        logger.info(f"触发联网搜索 | query: {query[:80]}")
        web_results = web_search(query, max_results=5)

        if not web_results or "搜索失败" in web_results[0].get("title", ""):
            return [doc for doc, _ in relevant[:k]] if relevant else [], False

        docs = results_to_documents(web_results)
        self.add_documents(docs, source="web")
        return self.search(query, k), True

    def _get_age_days(self, doc: Document) -> float:
        """文档从创建到现在过了多少天"""
        created = doc.metadata.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created)
            return (datetime.now() - created_dt).total_seconds() / 86400
        except (ValueError, TypeError):
            return 999  # 没有时间戳，视为非常旧

    def _get_max_age(self, doc: Document) -> int:
        """本地手写文档永不过期，联网搜来的 30 天过期"""
        if doc.metadata.get("source_type") == "local":
            return 999
        return WEB_CACHE_DAYS

    def as_retriever(self, k: int = 3):
        if self.vector_store is None:
            raise RuntimeError("知识库还没建，先调 build()")
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def stats(self) -> dict:
        """知识库统计"""
        if self.vector_store is None:
            return {"total": 0}
        total = self.vector_store._collection.count()
        return {
            "total": total,
            "persist_dir": self.persist_dir,
            "web_cache_days": WEB_CACHE_DAYS,
        }
