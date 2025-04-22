import os
import asyncio
from typing import Optional
from .retriever import SearchAPIRetriever, SectionRetriever
from langchain.retrievers import (
    ContextualCompressionRetriever,
)
from langchain.retrievers.document_compressors import (
    DocumentCompressorPipeline,
    EmbeddingsFilter,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..vector_store import VectorStoreWrapper
from ..memory.embeddings import OPENAI_EMBEDDING_MODEL


class VectorstoreCompressor:
    def __init__(self, vector_store: VectorStoreWrapper, max_results:int = 7, filter: Optional[dict] = None, **kwargs):

        self.vector_store = vector_store
        self.max_results = max_results
        self.filter = filter
        self.kwargs = kwargs

    def __pretty_print_docs(self, docs):
        return f"\n".join(f"Source: {d.metadata.get('source')}\n"
                          f"Title: {d.metadata.get('title')}\n"
                          f"Content: {d.page_content}\n"
                          for d in docs)

    async def async_get_context(self, query, max_results=5):
        """Get relevant context from vector store"""
        results = await self.vector_store.asimilarity_search(query=query, k=max_results, filter=self.filter)
        return self.__pretty_print_docs(results)


class ContextCompressor:
    def __init__(self, documents, embeddings, max_results=5, **kwargs):
        self.max_results = max_results
        self.documents = documents
        self.kwargs = kwargs
        self.embeddings = embeddings
        self.similarity_threshold = os.environ.get("SIMILARITY_THRESHOLD", 0.38)

    def __get_contextual_retriever(self):
        """创建一个上下文相关的文档检索器，将文本分割每个块为1000"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings,
                                            similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_retriever = SearchAPIRetriever(
            pages=self.documents
        )
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_retriever
        )
        return contextual_retriever

    def __pretty_print_docs(self, docs, top_n):
        return f"\n".join(f"Source: {d.metadata.get('source')}\n"
                          f"Title: {d.metadata.get('title')}\n"
                          f"Content: {d.page_content}\n"
                          for i, d in enumerate(docs) if i < top_n)

    async def async_get_context(self, query, max_results=5):
        """从一组文档中检索与给定查询相关的文档，并返回这些文档的格式化版本。以下是对代码功能的详细解释："""
        # compressed_docs = self.__get_contextual_retriever()
        # relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query)
        # # print("Relevant Docs:", relevant_docs)
        # return self.__pretty_print_docs(relevant_docs, max_results)
        try:
            compressed_docs = self.__get_contextual_retriever()
            relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query)
            return self.__pretty_print_docs(relevant_docs, max_results)
        except Exception as e:
            print("❌ async_get_context 出错:", e)
            raise


class WrittenContentCompressor:
    def __init__(self, documents, embeddings, similarity_threshold, **kwargs):
        self.documents = documents
        self.kwargs = kwargs
        self.embeddings = embeddings
        self.similarity_threshold = similarity_threshold

    def __get_contextual_retriever(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=self.embeddings,
                                            similarity_threshold=self.similarity_threshold)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_retriever = SectionRetriever(
            sections=self.documents
        )
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_retriever
        )
        return contextual_retriever

    def __pretty_docs_list(self, docs, top_n):
        return [f"Title: {d.metadata.get('section_title')}\nContent: {d.page_content}\n" for i, d in enumerate(docs) if i < top_n]

    async def async_get_context(self, query, max_results=5):
        compressed_docs = self.__get_contextual_retriever()
        relevant_docs = await asyncio.to_thread(compressed_docs.invoke, query)
        return self.__pretty_docs_list(relevant_docs, max_results)
