"""
爬虫 —— 搜索 → 抓取页面 → 提取正文 → 标题感知切分 → 入库

四层管道：
  1. DuckDuckGo 搜索 → 发现候选 URL
  2. requests + BeautifulSoup → 抓取整页 HTML → 提取正文
  3. split_by_headings() → 按文章标题结构拆分成语义段落
  4. 每段作为独立 Document 入库，标题作为前缀 + metadata
"""
import hashlib
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from utils.logging import get_logger

logger = get_logger("pipeline.crawler")

QUERY_TEMPLATES = [
    "{city} 旅游攻略",
    "{city} 必去景点 推荐",
    "{city} 美食 小吃 推荐",
    "{city} 交通 住宿 攻略",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
}

MIN_CONTENT_LENGTH = 200
PAGE_TIMEOUT = 10


def compute_content_hash(docs: list[Document]) -> str:
    combined = "".join(sorted(d.page_content for d in docs))
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def generate_queries(city: str, count: int = 4) -> list[str]:
    return [t.format(city=city) for t in QUERY_TEMPLATES[:count]]


def fetch_page(url: str, timeout: int = PAGE_TIMEOUT) -> str | None:
    """抓取整页 HTML，自动检测编码。失败返回 None。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        if resp.apparent_encoding:
            resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.RequestException as e:
        logger.debug(f"抓取失败 {url[:60]}: {e}")
        return None


def extract_content(html: str) -> str:
    """从 HTML 中提取正文，去除导航/广告/侧边栏/脚本/样式。"""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                     "noscript", "iframe", "form", "button", "img", "svg"]):
        tag.decompose()

    main = (
        soup.find("article") or
        soup.find("main") or
        soup.find(role="main") or
        soup.find(id=["content", "article", "main-content", "post-content"]) or
        soup.find(class_=["content", "article", "post-content", "entry-content",
                          "article-content", "post-body"]) or
        soup.find("body")
    )

    if main is None:
        return ""

    text = main.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return "\n".join(lines)


def split_by_headings(text: str) -> list[dict]:
    """
    按文章标题结构拆分成语义段落。

    支持的标题格式：
      - Markdown:  # 交通  / ## 景点推荐  / ### 注意事项
      - 中文编号:  一、行程安排  / 二、费用预算
      - 方括号:   【美食推荐】 / 【住宿攻略】
      - 数字列表:  1. 第一天  / 2. 第二天

    返回: [{"heading": "交通", "content": "西安地铁...", "style": "md"}, ...]
    无标题时返回单段 [{"heading": "", "content": text, "style": "none"}]
    """
    lines = text.split("\n")
    heading_positions = []  # [(line_index, heading_text, style), ...]

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        heading = None
        style = None

        # Markdown: # / ## / ### heading
        m = re.match(r"^#{1,3}\s+(.+)", line)
        if m:
            heading = m.group(1).strip()
            style = "md"

        # Chinese numbered: 一、xxx / 二、xxx
        if not heading:
            m = re.match(r"^[一二三四五六七八九十]+[、．.](.+)", line)
            if m:
                heading = f"{line[:2]} {m.group(1).strip()}"
                style = "cn_num"

        # Brackets: 【美食】 / 【交通攻略】
        if not heading:
            m = re.match(r"^【(.+?)】\s*$", line)
            if m:
                heading = m.group(1).strip()
                style = "bracket"

        # Numbered list: 1. xxx / 2、xxx (short line = heading, long line = sentence)
        if not heading:
            m = re.match(r"^(\d+)[\.、．]\s*(.+)", line)
            if m and len(m.group(2)) < 30:
                heading = m.group(2).strip()
                style = "num"

        if heading:
            heading_positions.append((i, heading, style))

    if len(heading_positions) < 2:
        return [{"heading": "", "content": text, "style": "none"}]

    sections = []
    for j, (line_idx, heading, style) in enumerate(heading_positions):
        start = line_idx + 1
        if j + 1 < len(heading_positions):
            end = heading_positions[j + 1][0]
        else:
            end = len(lines)

        content = "\n".join(lines[start:end]).strip()
        if not content:
            continue

        sections.append({"heading": heading, "content": content, "style": style})

    return sections if len(sections) >= 2 else [{"heading": "", "content": text, "style": "none"}]


def crawl_city(kb, city: str, max_results: int = 3, num_queries: int = 4) -> dict:
    """搜索 → 抓取页面全文 → diff → 入库。页面抓取失败时用搜索摘要兜底。"""
    from tools.search_tools import web_search, results_to_documents

    queries = generate_queries(city, num_queries)
    all_results = []
    seen_urls = set()

    for query in queries:
        try:
            results = web_search(query, max_results=max_results)
            if results and "搜索失败" not in results[0].get("title", ""):
                for r in results:
                    url = r.get("href", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"搜索失败 [{city}] query='{query}': {e}")
            continue

    if not all_results:
        logger.info(f"[{city}] 无搜索结果")
        return {"city": city, "added": 0, "changed": False}

    full_docs = []
    for r in all_results:
        url = r.get("href", "")
        title = r.get("title", "")
        if not url:
            continue
        try:
            html = fetch_page(url)
            if html:
                content = extract_content(html)
                if content and len(content) >= MIN_CONTENT_LENGTH:
                    sections = split_by_headings(content)
                    for sec in sections:
                        prefix = f"[{sec['heading']}] " if sec["heading"] else ""
                        text = f"标题：{title}\n{prefix}内容：{sec['content']}\n来源：{url}"
                        full_docs.append(Document(
                            page_content=text,
                            metadata={
                                "heading": sec["heading"],
                                "article_title": title,
                                "url": url,
                            },
                        ))
                    logger.debug(
                        f"[{city}] 抓取成功: {title[:40]} "
                        f"({len(content)} 字 → {len(sections)} 段)"
                    )
                else:
                    logger.debug(f"[{city}] 内容太短，跳过: {url[:60]}")
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"[{city}] 抓取异常 {url[:60]}: {e}")
            continue

    if not full_docs:
        logger.info(f"[{city}] 页面抓取全部失败，使用搜索摘要兜底")
        full_docs = results_to_documents(all_results)
        for doc in full_docs:
            doc.metadata["city"] = city

    return diff_and_update(kb, city, full_docs)


def diff_and_update(kb, city: str, new_docs: list[Document]) -> dict:
    """比对内容哈希，决定跳过 / 更新时间戳 / 删除重建。"""
    from db.database import get_fingerprint, upsert_fingerprint

    new_hash = compute_content_hash(new_docs)
    stored = get_fingerprint(city)

    if stored and stored["content_hash"] == new_hash:
        try:
            existing_ids = kb.get_doc_ids_by_city(city)
            if existing_ids:
                kb.update_timestamps(existing_ids, datetime.now().isoformat())
        except Exception as e:
            logger.debug(f"[{city}] 更新时间戳失败: {e}")
        logger.debug(f"[{city}] 内容未变化，跳过")
        return {"city": city, "added": 0, "changed": False}

    for doc in new_docs:
        doc.metadata["city"] = city

    # 先写入新数据，成功后再删旧的（防止写入失败导致数据丢失）
    count = kb.add_documents(new_docs, source="web")
    try:
        kb.delete_by_city(city)
    except Exception as e:
        logger.debug(f"[{city}] 清理旧数据失败: {e}")
    # 重新添加（因为 delete_by_city 可能删掉了刚写入的）
    count = kb.add_documents(new_docs, source="web")
    upsert_fingerprint(city, new_hash)
    logger.info(f"[{city}] 内容更新: {count} chunks")
    return {"city": city, "added": count, "changed": True}


def cleanup_expired(kb, max_age_days: int = 30) -> int:
    """删除所有超过 max_age_days 的 web 文档。"""
    cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
    try:
        collection = kb.vector_store._collection
        result = collection.get(
            where={"source_type": "web"},
            include=["metadatas"],
        )
        expired_ids = [
            id_
            for id_, m in zip(result["ids"], result["metadatas"])
            if m.get("created_at", "") < cutoff
        ]
        if expired_ids:
            collection.delete(ids=expired_ids)
            logger.info(f"清理 {len(expired_ids)} 条过期文档")
        return len(expired_ids)
    except Exception as e:
        logger.warning(f"清理过期数据失败: {e}")
        return 0


def get_all_cities(city_file: Path = None) -> list[str]:
    """从 pipeline/cities.txt 读取全国城市列表（~300 个地级市+热门旅游地）。"""
    if city_file is None:
        city_file = Path(__file__).parent / "cities.txt"

    if not city_file.exists():
        logger.warning(f"城市列表不存在: {city_file}")
        return _get_local_cities()

    cities = []
    with open(city_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                cities.append(line)
    return cities


def get_hot_cities(limit: int = 5) -> list[str]:
    """从 SQLite 热门目的地获取城市列表。"""
    from db.database import get_popular_cities

    popular = get_popular_cities(limit)
    return [p["city"] for p in popular]


def get_warm_cities(hot_cities: list[str] = None) -> list[str]:
    """全国城市列表，排除已在 hot 层的热门城市。"""
    hot = set(hot_cities or [])
    all_cities = get_all_cities()
    return [c for c in all_cities if c not in hot]


def _get_local_cities(data_dir: Path = None) -> list[str]:
    """回退方案：从 rag/data/*.txt 推断城市名（当 cities.txt 不存在时使用）。"""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "rag" / "data"

    city_map = {
        "xian": "西安",
        "guangzhou": "广州",
        "beijing": "北京",
        "chengdu": "成都",
        "hangzhou": "杭州",
        "shanghai": "上海",
        "shenzhen": "深圳",
        "chongqing": "重庆",
        "nanjing": "南京",
        "wuhan": "武汉",
    }

    cities = []
    for f in data_dir.glob("*.txt"):
        name = f.stem.lower()
        if "culture" in name or "tips" in name:
            continue
        pinyin = name.split("-")[0].split("_")[0]
        if pinyin in city_map:
            cities.append(city_map[pinyin])
        else:
            cities.append(pinyin)
    return cities
