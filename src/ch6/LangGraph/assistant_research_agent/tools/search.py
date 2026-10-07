"""搜索工具"""

from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

from project_optimization.add_log_monitor import log_tool_execution


@tool
@log_tool_execution("search_web")
def search_web(query: str) -> str:
    """使用 Tavily 搜索引擎搜索网络信息。当需要获取最新资讯、技术动态或公开信息时使用。

    query: 搜索关键词
    """
    try:
        import os
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            return "搜索失败: 未配置 TAVILY_API_KEY"

        tavily_client = TavilyClient(api_key=api_key)

        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )

        results = response.get("results", [])

        if not results:
            return "未找到相关结果"

        output = ""

        # Tavily AI 综合答案
        answer = response.get("answer")

        if answer:
            output += f"综合答案:\n{answer}\n\n"

        # 搜索结果
        output += "相关搜索结果:\n"

        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            score = r.get("score", 0)

            output += f"{i}. {title}\n"
            output += f"   URL: {url}\n"
            output += f"   相关性: {score:.2f}\n"
            output += f"   摘要: {content[:300]}\n\n"

        return output

    except Exception as e:
        return f"搜索失败: {e}"


@tool
@log_tool_execution("search_arxiv")
def search_arxiv(query: str) -> str:
    """搜索 arXiv 学术论文。当需要查找学术论文、研究成果时使用。

    query: 论文搜索关键词
    """
    try:
        import httpx

        url = "https://export.arxiv.org/api/query"

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 5,
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)

        entries = resp.text.split("<entry>")[1:]

        results = []

        for entry in entries[:5]:
            title = (
                entry.split("<title>")[1]
                .split("</title>")[0]
                .strip()
            )

            summary = (
                entry.split("<summary>")[1]
                .split("</summary>")[0]
                .strip()
            )

            results.append(
                f"- {title}\n"
                f"  摘要: {summary[:200]}"
            )

        return "\n\n".join(results) if results else "未找到相关论文"

    except Exception as e:
        return f"搜索失败: {e}"


if __name__ == "__main__":
    result = search_web.invoke({
        "query": "最新比特币价格"
    })

    print(result)