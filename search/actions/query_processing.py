import json_repair
from ..utils.llm import create_chat_completion
from ..prompts import generate_search_queries_prompt
from typing import Any, List, Dict
from ..config import Config
import logging

logger = logging.getLogger(__name__)

async def get_search_results(query: str, retriever: Any) -> List[Dict[str, Any]]:
    """
    获取给定查询的网页搜索结果
    
    Args:
        query: 搜索查询
        retriever: 检索器实例
    
    Returns:
        搜索结果列表
    """
    search_retriever = retriever(query)
    return search_retriever.search()

async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str,
    context: List[Dict[str, Any]],
    cfg: Config,
) -> List[str]:
    """
    使用指定的模型生成子查询
    
    Args:
        query: 原始查询
        parent_query: 父查询
        report_type: 报告类型
        max_iterations: 最大研究轮次
        context: 搜索结果上下文
        cfg: Configuration object
    
    Returns:
        子查询列表
    """
    gen_queries_prompt = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.max_iterations or 1,
        context=context
    )

    try:
        response = await create_chat_completion(
            model=cfg.strategic_model,
            messages=[{"role": "user", "content": gen_queries_prompt}],
            temperature=1,
            max_tokens=None,
            llm_kwargs=cfg.llm_kwargs,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e}. Falling back to smart LLM.")
        response = await create_chat_completion(
            model=cfg.smart_model,
            messages=[{"role": "user", "content": gen_queries_prompt}],
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            llm_kwargs=cfg.llm_kwargs,
        )

    return json_repair.loads(response)

async def plan_research_outline(
    query: str,
    search_results: List[Dict[str, Any]],
    agent_role_prompt: str,
    cfg: Config,
    parent_query: str,
    report_type: str,
) -> List[str]:
    """
    通过生成子查询规划研究大纲.
    
    Args:
        query: 原始查询
        retriever: 检索器实例
        agent_role_prompt: Agent role prompt
        cfg: 配置对象
        parent_query: 父查询
        report_type: 报告类型
    
    Returns:
        子查询列表
    """
    
    sub_queries = await generate_sub_queries(
        query,
        parent_query,
        report_type,
        search_results,
        cfg,
    )

    return sub_queries
