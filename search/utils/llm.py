# libraries
from __future__ import annotations

import json
import logging
from typing import Optional, Any, Dict

from colorama import Fore, Style
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from ..prompts import generate_subtopics_prompt
from .costs import estimate_llm_cost
from .validators import Subtopics


def get_llm( **kwargs):
    from MySearch.search.llm_provider import GenericLLMProvider
    return GenericLLMProvider.from_provider(**kwargs)


async def create_chat_completion(
        messages: list,  # type: ignore
        model: Optional[str] = None,
        temperature: Optional[float] = 0.4,
        max_tokens: Optional[int] = 4000,
        stream: Optional[bool] = False,
        websocket: Any | None = None,
        llm_kwargs: Dict[str, Any] | None = None,
        cost_callback: callable = None
) -> str:
    """使用 OpenAI API 创建聊天完成
        参数：
            messages (list[dict[str, str]]): 要发送到聊天完成的消息
            model (str, 可选): 要使用的模型。默认为 None。
            temperature (float, 可选): 要使用的温度。默认为 0.4。
            max_tokens (int, 可选): 要使用的最大 token 数。默认为 4000。
            stream (bool, 可选): 是否流式传输响应。默认为 False。
            llm_provider (str, 可选): 要使用的 LLM 提供者。
            websocket (WebSocket): 当前请求中使用的 websocket，
            cost_callback: 更新成本的回调函数
        返回：
            str: 聊天完成的响应
    """

    # validate input
    if model is None:
        raise ValueError("模型不能为空")
    if max_tokens is not None and max_tokens > 16001:
        raise ValueError(
            f"Max tokens cannot be more than 16,000, but got {max_tokens}")

    # Get the provider from supported providers
    provider = get_llm(model=model, temperature=temperature,
                       max_tokens=max_tokens, **(llm_kwargs or {}))

    response = ""
    # create response
    for _ in range(10):  # maximum of 10 attempts
        response = await provider.get_chat_response(
            messages, stream, websocket
        )

        if cost_callback:
            llm_costs = estimate_llm_cost(str(messages), response)
            cost_callback(llm_costs)

        return response

    logging.error(f"获取llm响应失败")
    raise RuntimeError(f"获取llm响应失败")


async def construct_subtopics(task: str, data: str, config, subtopics: list = []) -> list:
    """
        根据给定的任务和数据构建子主题。

        参数：
            task (str): 主要任务或主题。
            data (str): 用于上下文的附加数据。
            config: 配置设置。
            subtopics (list, 可选): 现有的子主题。默认为 []。

        返回：
            list: 构建的子主题列表。
    """

    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=generate_subtopics_prompt(),
            input_variables=["task", "data", "subtopics", "max_subtopics"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()},
        )

        print(f"\n🤖 正在调用 llm...prompt%s：\n",prompt)

        temperature = config.temperature
        # temperature = 0 # Note: temperature throughout the code base is currently set to Zero
        provider = get_llm(
            model=config.smart_model,
            temperature=temperature,
            max_tokens=config.max_tokens,
            **config.llm_kwargs,
        )
        model = provider.llm

        chain = prompt | model | parser

        output = chain.invoke({
            "task": task,
            "data": data,
            "subtopics": subtopics,
            "max_subtopics": config.max_subtopics
        })

        return output

    except Exception as e:
        print("Exception in parsing subtopics : ", e)
        return subtopics
