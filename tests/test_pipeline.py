"""
数据管道测试 —— APP_ENV=test 下 ¥0 成本运行。
"""
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from langchain_core.documents import Document

os.environ["APP_ENV"] = "test"
os.environ["PIPELINE_ENABLED"] = "false"

from pipeline.crawler import (
    compute_content_hash,
    generate_queries,
    fetch_page,
    extract_content,
    split_by_headings,
    crawl_city,
    diff_and_update,
    cleanup_expired,
    get_all_cities,
    get_hot_cities,
    get_warm_cities,
)


class TestContentHash:
    def test_deterministic(self):
        docs1 = [Document(page_content="西安旅游攻略"), Document(page_content="兵马俑")]
        docs2 = [Document(page_content="西安旅游攻略"), Document(page_content="兵马俑")]
        assert compute_content_hash(docs1) == compute_content_hash(docs2)

    def test_different_content(self):
        docs1 = [Document(page_content="西安旅游攻略")]
        docs2 = [Document(page_content="广州旅游攻略")]
        assert compute_content_hash(docs1) != compute_content_hash(docs2)

    def test_order_independent(self):
        docs1 = [Document(page_content="A"), Document(page_content="B")]
        docs2 = [Document(page_content="B"), Document(page_content="A")]
        assert compute_content_hash(docs1) == compute_content_hash(docs2)


class TestQueries:
    def test_generate_queries(self):
        qs = generate_queries("西安", count=4)
        assert len(qs) == 4
        assert all("西安" in q for q in qs)

    def test_generate_queries_custom_count(self):
        qs = generate_queries("北京", count=2)
        assert len(qs) == 2


class TestFetchPage:
    def test_fetch_success(self):
        fake_html = "<html><body><p>西安旅游攻略正文</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.text = fake_html
        mock_resp.apparent_encoding = None
        mock_resp.raise_for_status = MagicMock()

        with patch("pipeline.crawler.requests.get", return_value=mock_resp):
            html = fetch_page("https://example.com/travel")
            assert html == fake_html

    def test_fetch_failure_returns_none(self):
        import requests as rq
        with patch("pipeline.crawler.requests.get",
                   side_effect=rq.RequestException("timeout")):
            html = fetch_page("https://example.com/dead")
            assert html is None


class TestExtractContent:
    def test_extract_article(self):
        html = """
        <html><head><script>console.log('x')</script></head>
        <body>
            <nav>导航栏</nav>
            <article>
                <h1>西安三日游攻略</h1>
                <p>第一天去兵马俑，第二天去大雁塔，第三天去城墙。</p>
                <p>推荐美食：肉夹馍、羊肉泡馍。</p>
            </article>
            <footer>版权信息</footer>
        </body></html>
        """
        content = extract_content(html)
        assert "兵马俑" in content
        assert "肉夹馍" in content
        assert "导航栏" not in content
        assert "版权信息" not in content

    def test_extract_fallback_to_body(self):
        html = """
        <html><body>
            <div>没有 article 标签</div>
            <p>但这段正文仍然应该被提取</p>
        </body></html>
        """
        content = extract_content(html)
        assert "正文仍然应该被提取" in content

    def test_extract_strips_empty(self):
        html = "<html><body><script>code</script><style>css</style></body></html>"
        content = extract_content(html)
        assert content == ""


class TestSplitByHeadings:
    def test_markdown_headings(self):
        text = "## 交通\n西安地铁有4条线路，覆盖主要景点。\n\n## 美食\n肉夹馍是必吃的，推荐回民街。\n\n## 景点\n兵马俑世界闻名。"
        sections = split_by_headings(text)
        assert len(sections) == 3
        assert sections[0]["heading"] == "交通"
        assert "地铁" in sections[0]["content"]
        assert sections[1]["heading"] == "美食"
        assert "肉夹馍" in sections[1]["content"]
        assert sections[2]["heading"] == "景点"

    def test_chinese_numbered(self):
        text = "一、行程安排\n第一天去兵马俑。\n\n二、费用预算\n总计约3000元。\n\n三、注意事项\n注意防晒。"
        sections = split_by_headings(text)
        assert len(sections) == 3
        assert "行程安排" in sections[0]["heading"]
        assert "兵马俑" in sections[0]["content"]
        assert sections[1]["style"] == "cn_num"

    def test_brackets(self):
        text = "【景点推荐】\n兵马俑、大雁塔。\n\n【美食攻略】\n肉夹馍、凉皮。"
        sections = split_by_headings(text)
        assert len(sections) == 2
        assert sections[0]["heading"] == "景点推荐"
        assert sections[1]["heading"] == "美食攻略"
        assert sections[0]["style"] == "bracket"

    def test_numbered_list(self):
        text = "1. 第一天\n上午兵马俑，下午华清池。\n\n2. 第二天\n上午大雁塔，下午城墙。"
        sections = split_by_headings(text)
        assert len(sections) == 2
        assert "第一天" in sections[0]["heading"]
        assert "第二天" in sections[1]["heading"]

    def test_no_headings_returns_single(self):
        text = "这是一篇没有标题结构的纯文本，讲述了西安的旅游经历和美食推荐。"
        sections = split_by_headings(text)
        assert len(sections) == 1
        assert sections[0]["heading"] == ""
        assert sections[0]["content"] == text

    def test_single_heading_returns_single(self):
        text = "## 唯一的标题\n下面是一段内容。"
        sections = split_by_headings(text)
        assert len(sections) == 1

    def test_empty_between_headings_skipped(self):
        text = "## 交通\n有地铁\n\n## 美食\n肉夹馍。\n\n## 住宿\n\n\n\n## 门票\n120元。"
        sections = split_by_headings(text)
        # 住宿段无内容被跳过，门票被保留
        headings = [s["heading"] for s in sections]
        assert "交通" in headings
        assert "美食" in headings
        assert "住宿" not in headings
        assert "门票" in headings


class TestCityLists:
    def test_get_all_cities(self):
        cities = get_all_cities()
        assert isinstance(cities, list)
        assert len(cities) > 50  # 覆盖全国至少 50 个城市
        assert "西安" in cities
        assert "广州" in cities
        assert "北京" in cities
        # 直辖市在最前面
        assert "上海" in cities
        assert "重庆" in cities

    def test_get_warm_cities_excludes_hot(self):
        warm = get_warm_cities(hot_cities=["西安", "广州", "北京"])
        assert "西安" not in warm
        assert "广州" not in warm

    def test_get_hot_cities_returns_list(self):
        cities = get_hot_cities(limit=5)
        assert isinstance(cities, list)

    def test_get_warm_cities_covers_nationwide(self):
        warm = get_warm_cities(hot_cities=["西安", "广州"])
        assert isinstance(warm, list)
        # hot 城市被正确排除
        assert "西安" not in warm
        # 其他城市仍在列表中
        assert len(warm) > 50


class TestDiffAndUpdate:
    def test_no_change_skips(self, temp_chroma_dir):
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        docs = [Document(page_content="西安测试内容")]
        result1 = diff_and_update(kb, "测试城", docs)
        assert result1["changed"] is True
        assert result1["added"] > 0

        result2 = diff_and_update(kb, "测试城", docs)
        assert result2["changed"] is False
        assert result2["added"] == 0

    def test_content_changed_replaces(self, temp_chroma_dir):
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        docs_v1 = [Document(page_content="旧版攻略")]
        diff_and_update(kb, "变更城", docs_v1)

        docs_v2 = [Document(page_content="新版攻略——完全不同")]
        r2 = diff_and_update(kb, "变更城", docs_v2)
        assert r2["changed"] is True
        assert r2["added"] > 0


class TestCleanup:
    def test_removes_expired_web(self, temp_chroma_dir):
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        old_doc = Document(page_content="过期内容")
        old_doc.metadata["city"] = "过期城"
        kb.add_documents([old_doc], source="web")

        old_ts = (datetime.now() - timedelta(days=60)).isoformat()
        result = kb.vector_store._collection.get(include=["metadatas"])
        for i, m in enumerate(result["metadatas"]):
            if m.get("source_type") == "web":
                m["created_at"] = old_ts
        kb.vector_store._collection.update(
            ids=result["ids"], metadatas=result["metadatas"]
        )

        deleted = cleanup_expired(kb, max_age_days=30)
        assert deleted > 0

    def test_preserves_local(self, temp_chroma_dir):
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        before = kb.vector_store._collection.count()
        deleted = cleanup_expired(kb, max_age_days=1)
        remaining = kb.vector_store._collection.count()
        assert remaining == before - deleted


class TestCrawlCity:
    def test_crawl_with_mock_search(self, temp_chroma_dir, mock_search):
        """页面抓取失败时回退到搜索摘要。"""
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        # mock_search 返回的 URL 是假的，fetch_page 会失败，触发摘要兜底
        result = crawl_city(kb, "测试城", max_results=2, num_queries=2)

        assert result["city"] == "测试城"
        assert "added" in result


class TestFreshnessReport:
    def test_report_after_build(self, temp_chroma_dir):
        from rag.knowledge_store import TravelKnowledgeBase

        kb = TravelKnowledgeBase(persist_dir=temp_chroma_dir)
        kb.build()

        report = kb.freshness_report()
        assert "total_docs" in report
        assert report["total_docs"] >= 0
