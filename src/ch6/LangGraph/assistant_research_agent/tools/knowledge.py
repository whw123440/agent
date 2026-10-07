"""本地知识库工具（RAG）"""
from langchain_core.tools import tool
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


def build_vector_store(docs_dir: str, save_path: str):
    """从文档目录构建向量存储"""
    # 1. 加载文档
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.{txt,md}",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    # 2. 切分文档
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(docs)

    # 3. 创建向量存储
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=save_path,
    )
    return vectorstore


def get_retriever(docs_dir: str = "./data/knowledge", save_path: str = "./data/vector_store"):
    """获取检索器"""
    embeddings = OpenAIEmbeddings()

    # 尝试加载已有向量存储
    try:
        vectorstore = Chroma(
            persist_directory=save_path,
            embedding_function=embeddings,
        )
        # 检查是否有数据
        if vectorstore._collection.count() == 0:
            raise ValueError("空向量存储")
    except Exception:
        # 没有则重新构建
        vectorstore = build_vector_store(docs_dir, save_path)

    return vectorstore.as_retriever(search_kwargs={"k": 4})


# 初始化全局检索器（延迟加载）
_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = get_retriever()
    return _retriever


@tool
def search_knowledge_base(query: str) -> str:
    """从本地知识库中检索相关信息。
    当需要查询已有文档、内部资料、历史记录时使用。
    query: 检索关键词"""
    try:
        retriever = _get_retriever()
        docs = retriever.invoke(query)

        if not docs:
            return "知识库中未找到相关内容"

        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            results.append(f"[文档{i}] 来源: {source}\n{doc.page_content}")

        return "\n\n".join(results)
    except Exception as e:
        return f"知识库检索失败: {e}"