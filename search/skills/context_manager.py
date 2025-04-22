import asyncio
from typing import List, Dict, Optional, Set
from ..context.compression import ContextCompressor, WrittenContentCompressor, VectorstoreCompressor
from ..actions.utils import stream_output
class ContextManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher

    async def get_similar_content_by_query(self, query, pages):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_content",
                f"正在获取“{query}”相关内容..。。.",
                self.researcher.websocket,
            )
        print("执行到了相似度匹配fetching_query_content1")
        #计算与query的相似度，对检索到的context进行压缩
        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.researcher.memory.get_embeddings()
        )
        print("执行到了相似度匹配fetching_query_content2")
        #lgq相似度匹配结果设置
        return await context_compressor.async_get_context(
            query=query, max_results=7
        )
        
    async def get_similar_content_by_query_with_vectorstore(self, query, filter): 
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_format",
                f" 根据查询获取相关内容: {query}...",
                self.researcher.websocket,
                )
        vectorstore_compressor = VectorstoreCompressor(self.researcher.vector_store, filter)
        return await vectorstore_compressor.async_get_context(query=query, max_results=8)

    async def get_similar_content_by_query_with_vectorstore_web(self, query, pages, filter):
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_query_format",
                f" 根据查询获取相关内容: {query}...",
                self.researcher.websocket,
                )
        for page in pages:
            documents = self._process_document(self.report)

        context_compressor = ContextCompressor(
            documents=pages, embeddings=self.researcher.memory.get_embeddings()
        )
        vectorstore_compressor = VectorstoreCompressor(self.researcher.vector_store, filter)
        return await vectorstore_compressor.async_get_context(query=query, max_results=8)
    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        all_queries = [current_subtopic] + draft_section_titles

        async def process_query(query: str) -> Set[str]:
            return set(await self.__get_similar_written_contents_by_query(query, written_contents))

        results = await asyncio.gather(*[process_query(query) for query in all_queries])
        relevant_contents = set().union(*results)
        relevant_contents = list(relevant_contents)[:max_results]

        if relevant_contents and self.researcher.verbose:
            prettier_contents = "\n".join(relevant_contents)
            await stream_output(
                "logs", "relevant_contents_context", f"{prettier_contents}", self.researcher.websocket
            )

        return relevant_contents

    async def __get_similar_written_contents_by_query(self,
                                                      query: str,
                                                      written_contents: List[Dict],
                                                      similarity_threshold: float = 0.5,
                                                      max_results: int = 10
                                                      ) -> List[str]:
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "fetching_relevant_written_content",
                f"根据查询获取相关书面内容: {query}...",
                self.researcher.websocket,
            )

        written_content_compressor = WrittenContentCompressor(
            documents=written_contents,
            embeddings=self.researcher.memory.get_embeddings(),
            similarity_threshold=similarity_threshold
        )
        return await written_content_compressor.async_get_context(
            query=query, max_results=max_results
        )
