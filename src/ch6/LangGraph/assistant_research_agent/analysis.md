## 项目分析
### 项目结构
smart_research_assistant/
├── main.py              # 入口文件
├── config.py            # 配置文件
├── tools/
│   ├── __init__.py
│   ├── search.py        # 搜索工具
│   ├── file_ops.py      # 文件操作工具
│   └── knowledge.py     # 知识库工具（RAG）
├── agents/
│   ├── __init__.py
│   ├── supervisor.py    # 主管 Agent
│   ├── researcher.py    # 研究 Agent
│   ├── analyst.py       # 分析 Agent
│   └── writer.py        # 写作 Agent
├── graph.py             # LangGraph 工作流定义
├── state.py             # State 定义
└── data/
    └── knowledge/       # 本地知识库文档

图的执行流程
START
  ↓
[classify] ── simple ──→ [simple_answer] ──→ END
  ↓ research/report
[tool_calling]
  ↓ 有工具调用？
  ├── Yes → [tool_executor] → [collect]
  └── No  → [collect]
                ↓
           [researcher]
                ↓
            [analyst]
                ↓
            [writer]
                ↓
            [review] ── 未通过 ──→ [researcher]（循环）
                ↓ 通过
               END

16.12 关键设计回顾
本项目的架构贯穿了全书的核心概念：

┌─────────────────────────────────────────────────┐
│                  用户输入                         │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  LangGraph 工作流（第13-14章）                    │
│                                                   │
│  ┌──────────┐    ┌──────────┐                    │
│  │ classify │───→│ 简单回答  │ ← LCEL 管道（第5章） │
│  │ (路由)   │    └──────────┘                     │
│  └────┬─────┘                                     │
│       ↓                                           │
│  ┌──────────┐    ┌──────────┐                    │
│  │ 搜索工具  │←──→│ 工具执行  │ ← Tools（第9/12章） │
│  └────┬─────┘    └──────────┘                     │
│       ↓                                           │
│  ┌──────────┐                                     │
│  │ 研究节点  │ ← Prompt 模板（第3章）              │
│  └────┬─────┘                                     │
│       ↓                                           │
│  ┌──────────┐                                     │
│  │ 分析节点  │ ← LLM 调用（第2章）                 │
│  └────┬─────┘                                     │
│       ↓                                           │
│  ┌──────────┐                                     │
│  │ 写作节点  │ ← 输出解析（第4章）                 │
│  └────┬─────┘                                     │
│       ↓                                           │
│  ┌──────────┐                                     │
│  │ 质量审查  │──→ 未通过? → 回到研究（循环）        │
│  └────┬─────┘                                     │
│       ↓ 通过                                      │
└─────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────┐
│  输出结果 + 记忆持久化（第8/14章）                 │
└─────────────────────────────────────────────────┘
16.13 扩展方向
这个项目可以继续扩展：

方向	说明	涉及技术
Web 界面	用 Streamlit/Gradio 构建前端	Streamlit, Gradio
数据库持久化	用 SQLite/PostgreSQL 存储对话	LangGraph Checkpointer
更多工具	接入代码执行、图片生成等	Custom Tools
多语言支持	支持中英文研究	Prompt 设计
用户反馈	让用户评价报告质量	Human-in-the-Loop
邮件推送	自动发送研究报告	工具 + 工作流
API 服务	封装为 REST API	FastAPI
部署	Docker 容器化部署	Docker, CI/CD