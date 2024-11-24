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


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str
) -> float:
    """
    Calculate the cost of API usage based on the number of tokens and the model used.

    Args:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        model (str): The model used for the API call.

    Returns:
        float: The calculated cost in USD.
    """
    # Define cost per 1k tokens for different models
    costs = {
        "gpt-3.5-turbo": 0.002,
        "gpt-4": 0.03,
        "gpt-4-32k": 0.06,
        # Add more models and their costs as needed
    }

    model = model.lower()
    if model not in costs:
        logger.warning(
            f"Unknown model: {model}. Cost calculation may be inaccurate.")
        return 0.0

    cost_per_1k = costs[model]
    total_tokens = prompt_tokens + completion_tokens
    return (total_tokens / 1000) * cost_per_1k


def format_token_count(count: int) -> str:
    """
    Format the token count with commas for better readability.

    Args:
        count (int): The token count to format.

    Returns:
        str: The formatted token count.
    """
    return f"{count:,}"


async def update_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
    websocket: Any
) -> None:
    """
    Update and send the cost information through the WebSocket.

    Args:
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        model (str): The model used for the API call.
        websocket (WebSocket): The WebSocket connection to send data through.

    Returns:
        None
    """
    cost = calculate_cost(prompt_tokens, completion_tokens, model)
    total_tokens = prompt_tokens + completion_tokens

    await safe_send_json(websocket, {
        "type": "cost",
        "data": {
            "total_tokens": format_token_count(total_tokens),
            "prompt_tokens": format_token_count(prompt_tokens),
            "completion_tokens": format_token_count(completion_tokens),
            "total_cost": f"${cost:.4f}"
        }
    })


def create_cost_callback(websocket: Any) -> Callable:
    """
    Create a callback function for updating costs.

    Args:
        websocket (WebSocket): The WebSocket connection to send data through.

    Returns:
        Callable: A callback function that can be used to update costs.
    """
    async def cost_callback(
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> None:
        await update_cost(prompt_tokens, completion_tokens, model, websocket)

    return cost_callback
