"""准备知识库文档"""
import os

# 创建知识库目录
os.makedirs("./data/knowledge", exist_ok=True)

# 创建示例知识文档
with open("./data/knowledge/langchain-guide.md", "w", encoding="utf-8") as f:
    f.write("""# LangChain 开发指南

## 什么是 LangChain
LangChain 是一个用于开发大语言模型应用的开源框架。
它提供了模块化的组件，让开发者可以轻松构建 LLM 应用。

## 核心组件
- Model I/O: LLM 和 Chat Model 的接口
- Retrieval: RAG 检索增强生成的组件
- Chains: 链式调用
- Agents: 自主决策的 Agent
- Memory: 对话记忆

## LangGraph
LangGraph 是 LangChain 的扩展，专门用于构建有状态的、多角色的应用。
它基于图结构，支持循环、条件分支等复杂工作流。
""")

with open("./data/knowledge/agent-patterns.md", "w", encoding="utf-8") as f:
    f.write("""# Agent 设计模式

## ReAct 模式
ReAct (Reason + Act) 是最常用的 Agent 模式。
Agent 在每一步都先推理（Reason），然后行动（Act），
观察结果后再决定下一步。

## 多 Agent 模式
- Supervisor 模式：中心调度器分配任务
- Swarm 模式：Agent 间直接交接
- Hierarchical 模式：多层级管理

## 最佳实践
1. 工具描述要清晰，帮助 LLM 正确选择
2. 设置最大迭代次数，防止无限循环
3. 每个步骤的输入输出要可追踪
4. 使用 LangGraph 管理复杂工作流
""")