from typing import Dict, Any, Callable
from ..utils.logger import get_formatted_logger

logger = get_formatted_logger()


async def stream_output(
    type, content, output, websocket=None, output_log=True, metadata=None
):
    """
    将流失输出传输到WebSocket
    Args:
        type:输出类型
        content: 内容
        output: 输出内容

    Returns:
        None
    """
    if (not websocket or output_log) and type != "images":
        try:
            logger.info(f"{output}")
        except UnicodeEncodeError:
            # 选项 1: 用占位符替换有问题的字符
            logger.error(output.encode(
                'cp1252', errors='replace').decode('cp1252'))

    if websocket:
        await websocket.send_json(
            {"type": type, "content": content,
                "output": output, "metadata": metadata}
        )


async def safe_send_json(websocket: Any, data: Dict[str, Any]) -> None:
    """
    安全的通过WebSocket连接发送JSON数据

    Args:
        websocket (WebSocket): 要发送数据的 WebSocket 连接。
        data (Dict[str, Any]): 要发送的 JSON 数据。

    Returns:
        None
    """
    try:
        await websocket.send_json(data)
    except Exception as e:
        logger.error(f"通过 WebSocket 发送 JSON 时出错: {e}")


def format_token_count(count: int) -> str:
    """
    Format the token count with commas for better readability.

    Args:
        count (int): The token count to format.

    Returns:
        str: The formatted token count.
    """
    return f"{count:,}"
