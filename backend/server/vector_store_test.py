import asyncio

from langchain_chroma import Chroma
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from MySearch.search.config import Config
from MySearch.search.memory import Memory

from MySearch.search.vector_store import VectorStoreWrapper

print("数据库路径是否存在：", os.path.exists("./chroma_db"))

async def main():
    cfg = Config()
    memory = Memory(cfg.embedding_provider, cfg.embedding_model, **cfg.embedding_kwargs)
    embeddings = memory.get_embeddings()
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    vector_wrapper = VectorStoreWrapper(vector_store)
    # documents = [
    #     {"raw_content": "这是关于人工智能的介绍", "url": "http://example.com/ai"},
    #     {"raw_content": "机器学习是一种人工智能的子领域", "url": "http://example.com/ml"},
    #     {"raw_content": "深度学习是机器学习的一个分支", "url": "http://example.com/dl"},
    # ]
    # vector_wrapper.load(documents)
    query = "什么是人工智能？"
    results = await vector_wrapper.asimilarity_search(query=query, k=1, filter=None)
    for res in results:
        print(f"内容：{res.page_content},来源：{res.metadata['source']}")
    print("results", results)

asyncio.run(main())