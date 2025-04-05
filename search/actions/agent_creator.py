import json
import re
import json_repair
from ..utils.llm import create_chat_completion
from ..prompts import auto_agent_instructions

async def choose_agent(
    query, cfg, parent_query=None, headers=None
):
    """
    根据查询自动选择代理，并生成代理角色提示。
    Args:
        parent_query: 在某些情况下，搜索是在主查询的子主题上进行的。父查询允许代理知道主要上下文，以便更好地推理。
        query: 原始查询
        cfg: Config

    Returns:
        agent: Agent 名称
        agent_role_prompt: Agent 角色 prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response = None  # Initialize response to ensure it's defined

    try:
        response = await create_chat_completion(
            model=cfg.smart_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            temperature=0.15,
            llm_kwargs=cfg.llm_kwargs,
        )

        agent_dict = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]

    except Exception as e:
        print("⚠️ 读取 JSON 时出错，尝试修复 JSON")
        return await handle_json_error(response)


async def handle_json_error(response):
    try:
        agent_dict = json_repair.loads(response)
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):
            return agent_dict["server"], agent_dict["agent_role_prompt"]
    except Exception as e:
        print(f"使用 json_repair 时出错: {e}")

    json_string = extract_json_with_regex(response)
    if json_string:
        try:
            json_data = json.loads(json_string)
            return json_data["server"], json_data["agent_role_prompt"]
        except json.JSONDecodeError as e:
            print(f"解码 JSON 时出错: {e}")

    print("字符串中未找到 JSON。回退到默认代理。")
    return "Default Agent", (
        "你是一个 AI 批判性思维研究助手。你的唯一目的是编写高质量、客观且结构化的报告。"
    )


def extract_json_with_regex(response):
    json_match = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None