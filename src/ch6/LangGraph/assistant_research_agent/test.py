"""测试脚本"""
from graph import build_graph

graph = build_graph()
config = {"configurable": {"thread_id": "test-1"}}

# 测试1：简单问题
print("=== 测试1: 简单问题 ===")
result = graph.invoke(
    {"messages": [("user", "什么是 RAG？")]},
    config=config,
)

# 测试2：需要研究的问题
print("\n=== 测试2: 研究问题 ===")
result = graph.invoke(
    {"messages": [("user", "分析一下 LangChain 和 LangGraph 的关系和区别")]},
    config={"configurable": {"thread_id": "test-2"}},
)
if result.get("report"):
    print(result["report"])

# 测试3：需要搜索的深度问题
print("\n=== 测试3: 深度研究 ===")
result = graph.invoke(
    {"messages": [("user", "请研究 2024 年 AI Agent 领域的最新进展，并生成报告")]},
    config={"configurable": {"thread_id": "test-3"}},
)
if result.get("report"):
    print(result["report"][:500])

# 测试4：多轮对话（利用记忆）
print("\n=== 测试4: 多轮对话 ===")
config_multi = {"configurable": {"thread_id": "multi-1"}}

# 第一轮
graph.invoke(
    {"messages": [("user", "研究一下 Python 的异步编程")]},
    config=config_multi,
)

# 第二轮（追问，利用持久化的状态）
result = graph.invoke(
    {"messages": [("user", "基于之前的研究，详细解释 asyncio 的用法")]},
    config=config_multi,
)