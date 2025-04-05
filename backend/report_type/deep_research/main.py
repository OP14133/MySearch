import asyncio
import os
import sys

from MySearch.search.config import Config
from MySearch.search.memory import Memory
# from langchain.vectorstores import Chroma
from langchain_chroma import Chroma
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from MySearch.search.agent import GPTResearcher
from search.vector_store.siliconflow_embedding import SiliconFlowEmbeddings


async def main(task: str):
    # Progress callback
    def on_progress(progress):
        print(f"Depth: {progress.current_depth}/{progress.total_depth}")
        print(f"Breadth: {progress.current_breadth}/{progress.total_breadth}")
        print(f"Queries: {progress.completed_queries}/{progress.total_queries}")
        if progress.current_query:
            print(f"Current query: {progress.current_query}")

    cfg = Config()
    # os.environ["EMBEDDING_TOKEN"] = cfg.embedding_kwargs["token"]
    memory = Memory(cfg.embedding_provider, cfg.embedding_model, **cfg.embedding_kwargs)
    embeddings = memory.get_embeddings()
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    # Initialize researcher with deep research type
    researcher = GPTResearcher(
        query=task,
        report_type="deep",  # This will trigger deep research
        vector_store=vector_store,

    )
    # Run research with progress tracking
    print("Starting deep research...")
    context = await researcher.conduct_research(on_progress=on_progress)
    print("\nResearch completed. Generating report...")
    print("context————————————", context)
    # Generate the final report
    report = await researcher.write_report()
    # await write_md_to_pdf(report, "deep_research_report")
    print(f"\nFinal Report: {report}")

if __name__ == "__main__":
    query = "俄乌冲突"
    asyncio.run(main(query))