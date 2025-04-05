import json
import asyncio
from fastapi import WebSocket
from typing import Any
from ....database.schema import DialogueSchema, WebPageDetailsSchema
from ....search.actions import stream_output
from ....search.agent import GPTResearcher
from ....search.service.DialogueService import DialogueService
from ....search.utils.enum import ReportType


class BasicReport:
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
        # Initialize researcher
        researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            tone=self.tone,
            websocket=self.websocket,
            headers=self.headers,
            task_id=self.task_id,
        )

        self.sub_queries = researcher.sub_queries
        self.context = researcher.context

        await researcher.conduct_research()
        db =DialogueService()
        context = researcher.context
        research_source = researcher.research_sources
        visited_urls = researcher.visited_urls

        summery, timeline = await asyncio.gather(
            researcher.write_report_by_type(report_type=ReportType.SummeryReport.value),
            researcher.write_report_by_type(report_type=ReportType.TimeLineReport.value)
        )

        await stream_output(
            "timeline",
            timeline,
            researcher.websocket,
        )
        await self.websocket.send_json(
            {"type": "timeline","output": timeline}
        )
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
            timeline=timeline
        )
        db.create_dialogue(dialogue)
        return summery
