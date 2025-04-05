import random
import asyncio
import json_repair
from typing import Dict, List, Any
from ..prompts import generate_search_queries_prompt
from ..utils.llm import create_chat_completion
from ..context.compression import ContextCompressor
from ..actions.utils import stream_output
from ..actions.query_processing import get_search_results
from ..embeddings import Memory
from ..config import Config
# from MySearch.search.skills.browser import BrowserManager
from ..actions.retriever import get_retriever,get_retrievers
from ..actions.query_processing import *
from ..actions.web_scraping import scrape_urls
import logging
logger = logging.getLogger(__name__)
class WebSearch:
    def __init__(
            self,
            websocket: None,
            visited_urls: set = set(),
    ):
        self.websocket = websocket
        self.cfg = Config()
        self.retrievers = get_retrievers({}, self.cfg)
        self.visited_urls = visited_urls
        self.research_sources = []
        # self.scraper_manager: BrowserManager = BrowserManager(self)
    def add_research_sources(self, sources: List[Dict[str, Any]]) -> None:
        self.research_sources.extend(sources)
    async def get_context_by_search(self, query, scraped_data: list = []):
        """
        通过搜索查询抓取结果生成研究任务的上下文
        Returns:
            context: 上下文List
        """
        context = []
        # 生成包含原始查询的子查询
        sub_queries = await self.plan_research(query)

        #是否是详细模式，详细模式输出更多的日志信息
        await stream_output(
            "logs",
            "subqueries",
            f"我将基于以下子查询进行研究: {sub_queries}...",
            self.websocket,
            True,
            sub_queries,
        )
        # 使用 asyncio.gather 异步处理子查询
        context = await asyncio.gather(
            *[
                self.__process_sub_query(sub_query, scraped_data)
                for sub_query in sub_queries
            ]
        )
        print("context:",context)
        return context

    async def plan_research(self, query):
        await stream_output(
            "logs",
            "planning_research",
            f"浏览网页检索更多关于任务的信息: {query}...",
            self.websocket,
        )
        # retrievers = self.cfg.retrievers
        # retriever = get_retriever(retrievers[0])
        search_results = await get_search_results(query, self.retrievers[0])

        await stream_output(
            "logs",
            "planning_research",
            f"规划研究策略和子任务...",
            self.websocket,
        )
        return await plan_research_outline(
            query=query,
            search_results=search_results,
            # self.agent = "舆情信息检索代理"
            # self.role = "你是一位专业的舆情分析AI助手，负责基于给定问题和上下文，提取、整理并总结关键信息。你的任务是准确分析事件背景、传播动态、公众情绪和潜在影响，以结构化方式呈现，确保内容中立、全面且清晰。"
            agent_role_prompt="舆情信息检索代理",
            cfg=self.cfg,
            parent_query="",
            report_type="research_report",
        )
    async def __process_sub_query(self, sub_query: str, scraped_data: list = []):
        """接受子查询并根据抓取的urls收集上下文.

        Args:
            sub_query (str): 从原始查询生成的子查询
            scraped_data (list): 传入抓取的数据

        Returns:
            str: 从搜索中收集的上下文
        """

        await stream_output(
            "logs",
            "running_subquery_research",
            f"\n正在为子问题“'{sub_query}'”进行研究...",
            self.websocket,
        )

        if not scraped_data:
            scraped_data = await self.__scrape_data_by_query(sub_query)

        content = await self.get_similar_content_by_query(sub_query, scraped_data)
        await stream_output(
            "logs", "subquery_context_window", f"📃 {content[:1000]}", self.websocket
        )
        return content

    async def __get_new_urls(self, url_set_input):
        """从给定url集合中获取新的url集合，避免重复
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                new_urls.append(url)
                await stream_output(
                    "logs",
                    "added_source_url",
                    f"新增url: {url}\n",
                    self.websocket,
                    True,
                    url,
                )

        return new_urls

    async def __scrape_data_by_query(self, sub_query):
        """
        在多个检索器中运行子查询并抓取结果URL.

        Args:
            sub_query (str): 要搜索的子查询.

        Returns:
            list: 抓取到内容的结果列表.
        """
        new_search_urls = []

        # 遍历所有检索器

        for retriever_class in self.retrievers:
            # 使用子查询实例化检索器
            retriever = retriever_class(sub_query)

            # 使用当前检索器执行搜索
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.cfg.max_search_results_per_query
            )

            # 从搜索结果中收集新的url
            search_urls = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # 获取不重复的URLS
        new_search_urls = await self.__get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        # # 如果详细模式开启，记录研究过程

        await stream_output(
            "logs",
            "researching",
            f"在多个来源中研究相关信息...\n",
            self.websocket,
        )

        # 抓取新 URLS
        scraped_content = await self.browse_urls(new_search_urls)
        return scraped_content


    async def get_similar_content_by_query(self, query, pages):
        await stream_output(
            "logs",
            "fetching_query_content",
            f"正在获取“{query}”相关内容...",
            self.websocket,
        )

        embedding = Memory(
            self.cfg.embedding_provider,
            self.cfg.embedding_model,
            **self.cfg.embedding_kwargs
        ).get_embeddings()
        #计算与query的相似度，对检索到的context进行压缩
        context_compressor = ContextCompressor(
            documents=pages, embeddings=embedding
        )
        return await context_compressor.async_get_context(
            query=query, max_results=10
        )

    async def browse_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape content from a list of URLs.

        Args:
            urls (List[str]): List of URLs to scrape.

        Returns:
            List[Dict]: List of scraped content results.
        """
        await stream_output(
            "logs",
            "scraping_urls",
            f"正在从{len(urls)}个URL中爬取内容...",
            self.websocket,
        )
        scraped_content = scrape_urls(urls, self.cfg)
        self.add_research_sources(scraped_content)

        await stream_output(
            "logs",
            "scraping_content",
            f"抓取了 {len(scraped_content)} 页内容",
            self.websocket,
        )
        await stream_output(
            "logs",
            "scraping_complete",
            f"抓取完毕",
            self.websocket,
        )
        return scraped_content

