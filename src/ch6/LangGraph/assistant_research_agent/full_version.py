"""
智能研究助手 - 单文件完整版
综合运用: LCEL、RAG、Tools、Agent、LangGraph、Memory
"""

# ============================================================
# 1. State 定义
# ============================================================
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    question_type: str
    search_results: str
    research_notes: str
    analysis: str
    report: str
    iteration: int
    review_passed: bool
    next_agent: str


# ============================================================
# 2. 工具定义
# ============================================================
from langchain_core.tools import tool


@tool
def search_web(query: str) -> str:
    """搜索网络信息。query: 搜索关键词"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "未找到相关结果"
        return "\n\n".join(
            f"{i}. {r['title']}\n   {r['body'][:200]}"
            for i, r in enumerate(results, 1)
        )
    except Exception as e:
        return f"搜索失败: {e}"


@tool
def save_report(filename: str, content: str) -> str:
    """保存报告为 Markdown 文件"""
    import os
    os.makedirs("./data/reports", exist_ok=True)
    path = f"./data/reports/{filename}"
    if not path.endswith(".md"):
        path += ".md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已保存: {path}"


TOOLS = [search_web, save_report]


# ============================================================
# 3. 节点函数
# ============================================================
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate


def classify(state: ResearchState) -> dict:
    """分类问题"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    question = state["messages"][-1].content

    resp = llm.invoke([
        SystemMessage(content='回复一个词: simple/research/report'),
        HumanMessage(content=question),
    ])
    q_type = resp.content.strip().lower()
    if q_type not in ("simple", "research", "report"):
        q_type = "research"
    return {"question": question, "question_type": q_type}


def simple_answer(state: ResearchState) -> dict:
    """简单回答"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    resp = llm.invoke(state["messages"])
    return {"messages": [resp]}


def tool_call(state: ResearchState) -> dict:
    """调用搜索工具"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_tools = llm.bind_tools(TOOLS)
    resp = llm_tools.invoke([
        SystemMessage(content="搜索以下问题的信息。"),
        HumanMessage(content=state["question"]),
    ])
    return {"messages": [resp]}


def collect_results(state: ResearchState) -> dict:
    """收集搜索结果"""
    results = []
    for msg in state["messages"]:
        if hasattr(msg, "name") and msg.content:
            results.append(f"[{msg.name}] {msg.content[:500]}")
    return {"search_results": "\n\n".join(results)}


def research(state: ResearchState) -> dict:
    """研究分析"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是研究专家。整理信息，输出研究笔记。"),
        ("human", "问题: {question}\n\n搜索结果:\n{search}"),
    ])
    chain = prompt | llm
    resp = chain.invoke({
        "question": state["question"],
        "search": state.get("search_results", "无"),
    })
    return {"research_notes": resp.content}


def analyze(state: ResearchState) -> dict:
    """深度分析"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是分析专家。基于研究笔记进行深度分析。"),
        ("human", "问题: {question}\n\n笔记:\n{notes}"),
    ])
    chain = prompt | llm
    resp = chain.invoke({
        "question": state["question"],
        "notes": state.get("research_notes", ""),
    })
    return {"analysis": resp.content}


def write_report(state: ResearchState) -> dict:
    """撰写报告"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是写作专家。撰写一份 Markdown 格式的研究报告。
包含: 标题、摘要、关键发现、详细分析、结论。"""),
        ("human", "问题: {question}\n\n笔记:\n{notes}\n\n分析:\n{analysis}"),
    ])
    chain = prompt | llm
    resp = chain.invoke({
        "question": state["question"],
        "notes": state.get("research_notes", ""),
        "analysis": state.get("analysis", ""),
    })
    return {"report": resp.content}


def review(state: ResearchState) -> dict:
    """质量审查"""
    iteration = state.get("iteration", 0)
    if iteration >= 3:
        return {"review_passed": True, "iteration": iteration}

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    resp = llm.invoke([
        SystemMessage(content="审查报告。回复 PASS 或 REVISE。"),
        HumanMessage(content=f"问题: {state['question']}\n\n报告:\n{state.get('report', '')[:2000]}"),
    ])
    passed = "PASS" in resp.content.upper()[:10]
    return {"review_passed": passed, "iteration": iteration + 1}


# ============================================================
# 4. 路由函数
# ============================================================

def route_type(state: ResearchState) -> str:
    return "simple_answer" if state.get("question_type") == "simple" else "tool_call"


def route_tools(state: ResearchState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "executor"
    return "collect"


def route_review(state: ResearchState) -> str:
    return END if state.get("review_passed") else "research"


# ============================================================
# 5. 构建并运行
# ============================================================

def build():
    builder = StateGraph(ResearchState)

    builder.add_node("classify", classify)
    builder.add_node("simple_answer", simple_answer)
    builder.add_node("tool_call", tool_call)
    builder.add_node("executor", ToolNode(TOOLS))
    builder.add_node("collect", collect_results)
    builder.add_node("research", research)
    builder.add_node("analyze", analyze)
    builder.add_node("write", write_report)
    builder.add_node("review", review)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_type)
    builder.add_edge("simple_answer", END)
    builder.add_conditional_edges("tool_call", route_tools)
    builder.add_edge("executor", "collect")
    builder.add_edge("collect", "research")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.add_edge("write", "review")
    builder.add_conditional_edges("review", route_review)

    return builder.compile(checkpointer=MemorySaver())


# 运行
if __name__ == "__main__":
    graph = build()
    config = {"configurable": {"thread_id": "demo"}}

    # 简单问题
    print("=== 简单问题 ===")
    r = graph.invoke({"messages": [("user", "什么是 RAG？")]}, config)
    print(r["messages"][-1].content)

    # 研究问题
    print("\n=== 研究问题 ===")
    r = graph.invoke(
        {"messages": [("user", "研究 AI Agent 的最新进展并生成报告")]},
        config={"configurable": {"thread_id": "research-1"}},
    )
    if r.get("report"):
        print(r["report"])