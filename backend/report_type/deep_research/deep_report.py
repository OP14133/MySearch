import json
import asyncio

import websocket
from fastapi import WebSocket
from typing import Any

from langchain_chroma import Chroma

from database.schema import DialogueSchema
from ....search.analysis import wordcloud_tool
# from MySearch.database.schema import DialogueSchema, WebPageDetailsSchema
from ....search.actions import stream_output
from ....search.agent import GPTResearcher
from ....search.config import Config
from ....search.memory import Memory
from ....search.service.DialogueService import DialogueService
from ....search.utils.enum import ReportType


class DeepReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls,
        tone: Any,
        config_path: str,
        websocket: WebSocket,
        context: str,
        sub_queries: list,
        headers=None,
        task_id=str
    ):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.tone = tone
        self.config_path = config_path
        self.websocket = websocket
        self.headers = headers or {}
        self.context = context
        self.sub_queries = sub_queries
        self.task_id = task_id

        # self.db = Database()

    async def run(self):
        cfg = Config()
        memory = Memory(cfg.embedding_provider, cfg.embedding_model, **cfg.embedding_kwargs)
        embeddings = memory.get_embeddings()
        vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        # Initialize researcher with deep research type
        researcher = GPTResearcher(
            query=self.query,
            report_type="deep",  # This will trigger deep research
            vector_store=vector_store,
            websocket=self.websocket,
            headers=self.headers,

        )

        def on_progress(progress):
            print(f"Depth: {progress.current_depth}/{progress.total_depth}")
            print(f"Breadth: {progress.current_breadth}/{progress.total_breadth}")
            print(f"Queries: {progress.completed_queries}/{progress.total_queries}")
            if progress.current_query:
                print(f"Current query: {progress.current_query}")

        print("Starting deep research...")
        context = await researcher.conduct_research(on_progress=on_progress)
        print("\nResearch completed. Generating report...")
        # await researcher.conduct_research()
        db =DialogueService()
        context = researcher.context
        research_source = researcher.research_sources
        visited_urls = researcher.visited_urls

        summery, timeline, wordcloud = await asyncio.gather(
            researcher.write_report_by_type(report_type=ReportType.SummeryReport.value),
            researcher.write_report_by_type(report_type=ReportType.TimeLineReport.value),
            wordcloud_tool.generate_wordcloud_data(researcher.context, 60, researcher.websocket)
        )

#在上面输出
        # await stream_output(
        #     "timeline",
        #     timeline,
        #     researcher.websocket,
        # )
        # await self.websocket.send_json(
        #     {"type": "timeline","output": timeline}
        # )
        try:
            # 去除开头的 "json" 如果存在
            if timeline.strip().startswith("json"):
                timeline = timeline.strip()[4:].strip()
            timeline = json.loads(timeline)
        except json.JSONDecodeError:
            timeline = []

        dialogue = DialogueSchema(
            task_id=researcher.task_id,
            original_question=researcher.query,
            subqueries=researcher.sub_queries,
            urls=researcher.visited_urls,
            summery=summery,
            timeline=timeline,
            wordcloud=wordcloud
        )
        print("_____summery___",summery)
        db.create_dialogue(dialogue)
        return summery



