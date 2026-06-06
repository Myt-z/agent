"""
联网搜索 @tool —— Agent 的互联网眼睛

当本地知识库没有相关资料时，Agent 用这个工具实时搜索互联网。
搜索结果自动入库，下次再问同样的内容就走本地 RAG，秒回且免费。
"""

from langchain_core.tools import tool
from langchain_core.documents import Document


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    用 DuckDuckGo 搜索互联网（免费，无需 API Key）。

    返回: [{"title": ..., "body": ..., "href": ...}, ...]
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except ImportError:
        return [{"title": "错误", "body": "请先安装 ddgs: pip install ddgs", "href": ""}]
    except (ConnectionError, TimeoutError, OSError) as e:
        return [{"title": "搜索失败", "body": f"网络错误: {str(e)[:200]}", "href": ""}]
    except Exception as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit, MemoryError)):
            raise
        return [{"title": "搜索失败", "body": f"错误: {str(e)[:200]}", "href": ""}]


def results_to_documents(results: list[dict]) -> list[Document]:
    """将搜索结果转为 LangChain Document 对象"""
    docs = []
    for r in results:
        text = f"标题：{r.get('title', '')}\n内容：{r.get('body', '')}\n来源：{r.get('href', '')}"
        docs.append(Document(page_content=text))
    return docs


def format_search_results(results: list[dict]) -> str:
    """格式化搜索结果为可读文本，供 Agent 使用"""
    if not results:
        return "未搜到相关信息"

    lines = []
    for i, r in enumerate(results):
        title = r.get("title", "无标题")
        body = r.get("body", "")[:300]  # 截断，避免撑爆 prompt
        href = r.get("href", "")
        lines.append(f"[搜索结果{i+1}] {title}\n{body}...\n来源: {href}")

    return "\n\n".join(lines)
