from fastapi import WebSocket
from typing import Any

from MySearch.search.agent import GPTResearcher


class SearchReport:
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
        )
        self.sub_queries = researcher.sub_queries
        self.context = researcher.context
        await researcher.conduct_research()
        # researcher.rep
        report = await researcher.write_report()
        return report
