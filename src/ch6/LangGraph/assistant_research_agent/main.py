"""智能研究助手 - 主程序"""
import sys
from graph import build_graph


def interactive_mode(graph):
    """交互式对话模式"""
    print("=" * 50)
    print("智能研究助手 v1.0")
    print("输入问题开始研究，输入 'quit' 退出")
    print("=" * 50)

    thread_id = "session-1"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        # 调用图
        result = graph.invoke(
            {"messages": [("user", user_input)]},
            config=config,
        )

        # 输出结果
        print("\n" + "=" * 40)

        if result.get("report"):
            print("研究报告:")
            print(result["report"])
        else:
            # 简单回答
            for msg in result["messages"]:
                if hasattr(msg, "content") and msg.content:
                    # 只输出最后的 AI 回复
                    pass
            last_ai = None
            for msg in result["messages"]:
                if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                    last_ai = msg.content
            if last_ai:
                print(f"AI: {last_ai}")

        print("=" * 40)


def single_query(graph, question: str):
    """单次查询模式"""
    config = {"configurable": {"thread_id": "single"}}

    result = graph.invoke(
        {"messages": [("user", question)]},
        config=config,
    )

    if result.get("report"):
        print(result["report"])
    else:
        for msg in result["messages"]:
            if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                print(msg.content)


def stream_mode(graph, question: str):
    """流式输出模式"""
    config = {"configurable": {"thread_id": "stream"}}

    print(f"问题: {question}\n")
    print("处理中...")

    for event in graph.stream(
        {"messages": [("user", question)]},
        config=config,
    ):
        for node_name, output in event.items():
            print(f"\n[{node_name}]")
            if "report" in output:
                print(output["report"][:200] + "...")
            elif "research_notes" in output:
                print(f"研究笔记: {output['research_notes'][:200]}...")
            elif "analysis" in output:
                print(f"分析: {output['analysis'][:200]}...")

    print("\n完成!")


if __name__ == "__main__":
    graph = build_graph()

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        single_query(graph, query)
    else:
        interactive_mode(graph)