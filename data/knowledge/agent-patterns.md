# Agent 设计模式

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
