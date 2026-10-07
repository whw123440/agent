"""项目配置"""
import os

# LLM 配置
LLM_MODEL = "Qwen/Qwen3.5-35B-A3B"
LLM_TEMPERATURE = 0

# 检索配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4

# 向量存储
VECTOR_STORE_PATH = "./data/vector_store"

# 持久化
CHECKPOINT_DB_PATH = "./data/checkpoints.db"

# 最大研究轮次
MAX_RESEARCH_ITERATIONS = 3