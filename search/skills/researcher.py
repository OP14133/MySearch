import asyncio
import random
import json
from typing import Dict, Optional

from ..actions.utils import stream_output
from ..actions.query_processing import plan_research_outline, get_search_results
from ..document import DocumentLoader, LangChainDocumentLoader
from ..utils.enum import ReportSource, ReportType, Tone


class ResearchConductor:
    """管理和协调研究过程"""

    def __init__(self, researcher):
        self.researcher = researcher

    async def conduct_research(self):
        """
        运行GPT Researcher 进行研究
        Runs the GPT Researcher to conduct research
        """
        # 在每次研究任务开始时重置 visited_urls 和 source_urls
        self.researcher.visited_urls.clear()
        # 由于 report_type 被 report_source 取代，
        # 如果 report_source 不是 static，我们需要清空 source_urls
        if self.researcher.report_source != "static" and self.researcher.report_type != "sources":
            self.researcher.source_urls = []

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "starting_research",
                f"🔎 Starting the research task for '{self.researcher.query}'...",
                self.researcher.websocket,
            )

        if self.researcher.verbose:
            await stream_output("logs", "agent_generated", self.researcher.agent, self.researcher.websocket)

        # 如果指定了，研究者将使用给定的 urls 作为研究的上下文。
        if self.researcher.source_urls:
            self.researcher.context = await self.__get_context_by_urls(self.researcher.source_urls)

        elif self.researcher.report_source == ReportSource.Local.value:
            document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)

            self.researcher.context = await self.__get_context_by_search(self.researcher.query, document_data)

        # 混合搜索，包括本地文档和网页来源
        elif self.researcher.report_source == ReportSource.Hybrid.value:
            document_data = await DocumentLoader(self.researcher.cfg.doc_path).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(document_data)
            docs_context = await self.__get_context_by_search(self.researcher.query, document_data)
            web_context = await self.__get_context_by_search(self.researcher.query)
            self.researcher.context = f"本地文档的上下文: {docs_context}\n\n网页来源的上下文: {web_context}"

        elif self.researcher.report_source == ReportSource.LangChainDocuments.value:
            langchain_documents_data = await LangChainDocumentLoader(
                self.researcher.documents
            ).load()
            if self.researcher.vector_store:
                self.researcher.vector_store.load(langchain_documents_data)
            self.researcher.context = await self.__get_context_by_search(
                self.researcher.query, langchain_documents_data
            )

        elif self.researcher.report_source == ReportSource.LangChainVectorStore.value:
            self.researcher.context = await self.__get_context_by_vectorstore(self.researcher.query, self.researcher.vector_store_filter)
        # 默认的基于网页的研究
        else:
            self.researcher.context = await self.__get_context_by_search(self.researcher.query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "research_step_finalized",
                f"研究步骤已完成.\n💸 总研究成本: ${self.researcher.get_costs()}",
                self.researcher.websocket,
            )

        return self.researcher.context

    async def __get_context_by_urls(self, urls):
        """
        从给定的urls中抓取并压缩上下文，存入向量数据库，生成与查询相关的上下文（就是对多个url的内容进行提取并压缩）
        """
        new_search_urls = await self.__get_new_urls(urls)
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "source_urls",
                f"🗂️ 我将基于以下 URL 进行研究: {new_search_urls}...",
                self.researcher.websocket,
            )

        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_content)

        return await self.researcher.context_manager.get_similar_content_by_query(self.researcher.query, scraped_content)

    async def __get_context_by_vectorstore(self, query, filter: Optional[dict] = None):
        """
        通过向量存储生成研究任务的上下文
        Returns:
            context: List of context
        """
        context = []
        # 生成包含原始查询的子查询
        sub_queries = await self.plan_research(query)
        # 如果这不是子研究的一部分，添加原始查询以获得更好的结果
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️  我将基于以下查询进行研究: {sub_queries}...",
                self.researcher.websocket,
                True,
                sub_queries,
            )

        # 使用 asyncio.gather 异步处理子查询
        context = await asyncio.gather(
            *[
                self.__process_sub_query_with_vectorstore(sub_query, filter)
                for sub_query in sub_queries
            ]
        )
        return context

    async def __get_context_by_search(self, query, scraped_data: list = []):
        """
        通过搜索查询抓取结果生成研究任务的上下文
        Returns:
            context: 上下文List
        """
        context = []
        # 生成包含原始查询的子查询
        sub_queries = await self.plan_research(query)
        # 如果这不是子研究的一部分，添加原始查询以获得更好的结果
        if self.researcher.report_type != "subtopic_report":
            sub_queries.append(query)

        #是否是详细模式，详细模式输出更多的日志信息
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subqueries",
                f"🗂️ 我将基于以下查询进行研究: {sub_queries}...",
                self.researcher.websocket,
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
        return context

    async def __process_sub_query_with_vectorstore(self, sub_query: str, filter: Optional[dict] = None):
        """接受子查询并从用户提供的向量存储中收集上下文

        Args:
            sub_query (str): 从原始问题查询生成的子查询

        Returns:
            str: 从搜索中收集的上下文
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_with_vectorstore_research",
                f"\n🔍 正在为 '{sub_query}'进行研究...",
                self.researcher.websocket,
            )

        content = await self.researcher.context_manager.get_similar_content_by_query_with_vectorstore(sub_query, filter)

        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 未找到 '{sub_query}'的内容...",
                self.researcher.websocket,
            )
        return content

    async def __process_sub_query(self, sub_query: str, scraped_data: list = []):
        """接受子查询并根据抓取的urls收集上下文.

        Args:
            sub_query (str): 从原始查询生成的子查询
            scraped_data (list): 传入抓取的数据

        Returns:
            str: 从搜索中收集的上下文
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "running_subquery_research",
                f"\n🔍 正在为 '{sub_query}'进行研究...",
                self.researcher.websocket,
            )

        if not scraped_data:
            scraped_data = await self.__scrape_data_by_query(sub_query)

        content = await self.researcher.context_manager.get_similar_content_by_query(sub_query, scraped_data)
        if content and self.researcher.verbose:
            await stream_output(
                "logs", "subquery_context_window", f"📃 {content}", self.researcher.websocket
            )
        elif self.researcher.verbose:
            await stream_output(
                "logs",
                "subquery_context_not_found",
                f"🤷 未找到 '{sub_query}'的内容...",
                self.researcher.websocket,
            )
        return content

    async def __get_new_urls(self, url_set_input):
        """从给定url集合中获取新的url集合，避免重复
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.researcher.visited_urls:
                self.researcher.visited_urls.add(url)
                new_urls.append(url)
                if self.researcher.verbose:
                    await stream_output(
                        "logs",
                        "added_source_url",
                        f"✅ Added source url to research: {url}\n",
                        self.researcher.websocket,
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
        for retriever_class in self.researcher.retrievers:
            # 使用子查询实例化检索器
            retriever = retriever_class(sub_query)

            # 使用当前检索器执行搜索
            search_results = await asyncio.to_thread(
                retriever.search, max_results=self.researcher.cfg.max_search_results_per_query
            )

            # 从搜索结果中收集新的url
            search_urls = [url.get("href") for url in search_results]
            new_search_urls.extend(search_urls)

        # 获取不重复的URLS
        new_search_urls = await self.__get_new_urls(new_search_urls)
        random.shuffle(new_search_urls)

        # # 如果详细模式开启，记录研究过程
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "researching",
                f"🤔 在多个来源中研究相关信息...\n",
                self.researcher.websocket,
            )

        # 抓取新 URLS
        scraped_content = await self.researcher.scraper_manager.browse_urls(new_search_urls)

        if self.researcher.vector_store:
            self.researcher.vector_store.load(scraped_content)

        return scraped_content

    async def plan_research(self, query):
        await stream_output(
            "logs",
            "planning_research",
            f"🌐 浏览网页以了解更多关于任务的信息: {query}...",
            self.researcher.websocket,
        )

        search_results = await get_search_results(query, self.researcher.retrievers[0])

        await stream_output(
            "logs",
            "planning_research",
            f"🤔 规划研究策略和子任务 (这可能需要一分钟)...",
            self.researcher.websocket,
        )

        return await plan_research_outline(
            query=query,
            search_results=search_results,
            agent_role_prompt=self.researcher.role,
            cfg=self.researcher.cfg,
            parent_query=self.researcher.parent_query,
            report_type=self.researcher.report_type,
            cost_callback=self.researcher.add_costs,
        )
