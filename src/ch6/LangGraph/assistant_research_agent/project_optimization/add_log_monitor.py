"""日志与监控工具"""

import time
import logging
import functools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -[%(name)s]- %(levelname)s - %(message)s"
)

logger = logging.getLogger("research_assistant")


# ============================================================
# LangGraph 节点日志装饰器
# ============================================================

def log_node_execution(node_name: str):
    """记录 LangGraph 节点执行时间和结果"""

    def decorator(func):

        @functools.wraps(func)
        def wrapper(state):
            logger.info(f"[{node_name}] 开始执行")

            start = time.time()

            try:
                # 普通 LangGraph 节点
                result = func(state)

                elapsed = time.time() - start
                logger.info(
                    f"[{node_name}] 完成, 耗时 {elapsed:.2f}s"
                )

                log_result(node_name, result)

                return result

            except Exception as e:
                elapsed = time.time() - start

                logger.exception(
                    f"[{node_name}] 执行失败, 耗时 {elapsed:.2f}s"
                )

                raise

        return wrapper

    return decorator


# ============================================================
# LangChain Tool 日志装饰器
# ============================================================

def log_tool_execution(tool_name: str):
    """记录 LangChain Tool 执行时间和结果"""

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            logger.info(f"[{tool_name}] 工具开始执行")

            start = time.time()

            try:
                # -----------------------------------------
                # 情况1：普通 Python 函数
                # -----------------------------------------
                if callable(func):
                    result = func(*args, **kwargs)

                # -----------------------------------------
                # 情况2：LangChain StructuredTool
                # -----------------------------------------
                elif hasattr(func, "invoke"):
                    if kwargs:
                        result = func.invoke(kwargs)
                    elif len(args) == 1:
                        result = func.invoke(args[0])
                    else:
                        result = func.invoke(args)

                else:
                    raise TypeError(
                        f"{tool_name} 不支持调用，类型：{type(func)}"
                    )

                elapsed = time.time() - start

                logger.info(
                    f"[{tool_name}] 工具完成, 耗时 {elapsed:.2f}s"
                )

                log_result(tool_name, result)

                return result

            except Exception:
                elapsed = time.time() - start

                logger.exception(
                    f"[{tool_name}] 工具执行失败, 耗时 {elapsed:.2f}s"
                )

                raise

        return wrapper

    return decorator


# ============================================================
# 统一结果日志
# ============================================================

def log_result(name: str, result):
    """统一记录节点/工具返回结果"""

    if isinstance(result, dict):

        for key, value in result.items():

            if isinstance(value, str):
                logger.info(
                    f"[{name}] 输出 {key}: {len(value)} 字符"
                )

            elif isinstance(value, list):
                logger.info(
                    f"[{name}] 输出 {key}: {len(value)} 项"
                )

            else:
                logger.info(
                    f"[{name}] 输出 {key}: {type(value).__name__}"
                )

    elif isinstance(result, list):

        logger.info(
            f"[{name}] 输出: {len(result)} 项"
        )

    elif isinstance(result, str):

        logger.info(
            f"[{name}] 输出: {result}"
        )

    else:

        logger.info(
            f"[{name}] 输出类型: {type(result).__name__}"
        )