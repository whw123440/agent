from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from tavily import TavilyClient


# =========================
# 1. State
# =========================

class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    search_query: str
    search_results: str
    final_answer: str
    step: str


# =========================
# 2. 加载环境变量
# =========================

load_dotenv()


# =========================
# 3. 初始化 LLM
# =========================

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID", "gpt-4o-mini"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv(
        "LLM_BASE_URL",
        "https://api.openai.com/v1"
    ),
    temperature=0.7
)


# =========================
# 4. 初始化 Tavily
# =========================

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================
# 5. 理解用户问题
# =========================

def understand_query_node(state: SearchState) -> dict:

    user_message = state["messages"][-1].content

    understand_prompt = f"""
你是一个搜索需求分析助手。

分析用户的问题：

{user_message}

请完成两个任务：

1. 简洁总结用户真正想了解什么
2. 生成适合 Tavily 搜索的精准搜索关键词

严格按照以下格式输出：

理解：[用户需求总结]
搜索词：[最佳搜索关键词]
"""

    response = llm.invoke([
        SystemMessage(content=understand_prompt)
    ])

    response_text = response.content

    # 默认值
    user_query = user_message
    search_query = user_message

    # 提取理解结果
    if "理解：" in response_text:
        user_query = response_text.split("理解：", 1)[1]

        if "搜索词：" in user_query:
            user_query = user_query.split(
                "搜索词：",
                1
            )[0].strip()

    # 提取搜索关键词
    if "搜索词：" in response_text:
        search_query = response_text.split(
            "搜索词：",
            1
        )[1].strip()

    print("\n========== 查询理解 ==========")
    print("用户需求：", user_query)
    print("搜索关键词：", search_query)

    return {
        "user_query": user_query,
        "search_query": search_query,
        "step": "understood",
        "messages": [
            AIMessage(
                content=f"我将为您搜索：{search_query}"
            )
        ]
    }


# =========================
# 6. Tavily 搜索
# =========================

def tavily_search_node(state: SearchState) -> dict:

    search_query = state["search_query"]

    try:

        print("\n========== Tavily 搜索 ==========")
        print("搜索：", search_query)

        response = tavily_client.search(
            query=search_query,
            search_depth="basic",
            max_results=5,
            include_answer=True
        )

        results = response.get("results", [])

        if not results:
            return {
                "search_results": "没有找到相关搜索结果。",
                "step": "searched",
                "messages": [
                    AIMessage(
                        content="没有找到相关搜索结果。"
                    )
                ]
            }

        formatted_results = []

        for i, item in enumerate(results, 1):

            formatted_results.append(
                f"""
===== 搜索结果 {i} =====
标题：{item.get("title", "")}
链接：{item.get("url", "")}
内容：
{item.get("content", "")}
"""
            )

        search_results = "\n".join(formatted_results)

        print("\n搜索结果数量：", len(results))

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [
                AIMessage(
                    content="搜索完成，正在整理答案..."
                )
            ]
        }

    except Exception as e:

        print("\nTavily 搜索失败：", e)

        return {
            "search_results": f"搜索失败：{str(e)}",
            "step": "search_failed",
            "messages": [
                AIMessage(
                    content="搜索遇到问题，将尝试使用模型知识回答。"
                )
            ]
        }


# =========================
# 7. 生成最终答案
# =========================

def generate_answer_node(state: SearchState) -> dict:

    if state["step"] == "search_failed":

        prompt = f"""
搜索 API 暂时不可用。

请基于你的知识回答用户的问题。

用户问题：
{state["user_query"]}
"""

    else:

        prompt = f"""
你是一名专业的信息分析助手。

请根据下面的搜索结果回答用户的问题。

用户需求：
{state["user_query"]}

搜索结果：
{state["search_results"]}

要求：

1. 优先使用搜索结果中的信息
2. 不要编造不存在的信息
3. 对多个来源的信息进行综合
4. 回答结构清晰
5. 如果搜索结果不足以回答问题，要明确说明
"""

    response = llm.invoke([
        SystemMessage(content=prompt)
    ])

    print("\n========== 最终答案 ==========")
    print(response.content)

    return {
        "final_answer": response.content,
        "step": "completed",
        "messages": [
            AIMessage(content=response.content)
        ]
    }


# =========================
# 8. 创建 LangGraph
# =========================

def create_search_assistant():

    workflow = StateGraph(SearchState)

    workflow.add_node(
        "understand",
        understand_query_node
    )

    workflow.add_node(
        "search",
        tavily_search_node
    )

    workflow.add_node(
        "answer",
        generate_answer_node
    )

    workflow.add_edge(
        START,
        "understand"
    )

    workflow.add_edge(
        "understand",
        "search"
    )

    workflow.add_edge(
        "search",
        "answer"
    )

    workflow.add_edge(
        "answer",
        END
    )

    memory = InMemorySaver()

    app = workflow.compile(
        checkpointer=memory
    )

    return app


# =========================
# 9. 测试
# =========================

if __name__ == "__main__":

    app = create_search_assistant()

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="2026年最新的AI大模型有哪些重要进展？"
                )
            ],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": ""
        },
        config={
            "configurable": {
                "thread_id": "test-001"
            }
        }
    )

    print("\n================================")
    print("最终结果：")
    print(result["final_answer"])
    print("================================")