"""
Wrapper for langchain vector store
"""
from typing import List, Dict

from langchain.docstore.document import Document
from langchain.vectorstores import VectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStoreWrapper:
    """
    A Wrapper for LangchainVectorStore to handle GPT-Researcher Document Type
    """
    def __init__(self, vector_store : VectorStore):
        self.vector_store = vector_store

    def load(self, documents):
        """
        Load the documents into vector_store
        Translate to langchain doc type, split to chunks then load
        """
        langchain_documents = self._create_langchain_documents(documents)
        splitted_documents = self._split_documents(langchain_documents)
        # print("文档数量load前：", self.vector_store._collection.count())
        # print("示例文档load前：", self.vector_store.get(limit=2))
        # self.vector_store.add_documents(splitted_documents)
        # print("文档数量load后：", self.vector_store._collection.count())
        # print("示例文档load后", self.vector_store.get(limit=2))
        # # print("当前存储的文档数量：", self.vector_store._collection.count())
        # 判断是否是
        # VectorStoreWrapper
        # 类型
        if isinstance(self.vector_store, VectorStoreWrapper):
            store = self.vector_store.vector_store  # 访问真实的 vector store
        else:
            store = self.vector_store

        # try:
        #     print("文档数量load前：", store._collection.count())
        # except AttributeError:
        #     print("警告：当前 vector_store 没有 _collection 属性，无法获取文档数量")
        #
        # try:
        #     print("示例文档load前：", store.get(limit=2))
        # except Exception as e:
        #     print("获取示例文档失败：", str(e))

        store.add_documents(splitted_documents)

        # print("文档数量load后：", store._collection.count())
        # print("示例文档load后", store.get(limit=2))
    
    def _create_langchain_documents(self, data: List[Dict[str, str]]) -> List[Document]:
        """Convert GPT Researcher Document to Langchain Document"""
        return [Document(page_content=item["raw_content"], metadata={"source": item["url"]}) for item in data]

    def _split_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        """
        Split documents into smaller chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return text_splitter.split_documents(documents)

    async def asimilarity_search(self, query, k, filter):
        """Return query by vector store"""
        results = await self.vector_store.asimilarity_search(query=query, k=k, filter=filter)
        return results
