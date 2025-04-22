from typing import Optional, List, Dict, Any, Set
import json

from .config import Config
from .memory import Memory
from .skills.curator import SourceCurator
from .skills.deep_research import DeepResearchSkill
from .utils.enum import ReportSource, ReportType, Tone
from .llm_provider import GenericLLMProvider
from .vector_store import VectorStoreWrapper

# Research skills
from .skills.researcher import ResearchConductor
from .skills.writer import ReportGenerator
from .skills.context_manager import ContextManager
from .skills.browser import BrowserManager
from .service.DialogueService import DialogueService
from .actions import (
    add_references,
    extract_headers,
    extract_sections,
    table_of_contents,
    get_retrievers,
)


class GPTResearcher:
    def __init__(
        self,
        query: str,
        report_type: str = ReportType.ResearchReport.value,
        report_format: str = "markdown",
        report_source: str = ReportSource.Web.value,
        tone: Tone = Tone.Objective,
        is_deep: int = 0,
        source_urls=None,
        documents=None,
        vector_store=None,
        vector_store_filter=None,
        websocket=None,
        agent=None,
        role=None,
        parent_query: str = "",
        subtopics: list = [],
        visited_urls: set = set(),
        verbose: bool = True,
        context=[],
        headers: dict = None,
        max_subtopics: int = 2,
        task_id=str,
    ):
        self.query = query
        self.report_type = report_type
        self.cfg = Config()
        self.llm = GenericLLMProvider(self.cfg)
        self.report_source = getattr(
            self.cfg, 'report_source', None) or report_source
        self.report_format = report_format
        self.max_subtopics = max_subtopics
        self.tone = tone if isinstance(tone, Tone) else Tone.Objective
        self.source_urls = source_urls
        self.research_sources = []  # The list of scraped sources including title, content and images
        self.research_images = []  # The list of selected research images
        self.documents = documents
        self.vector_store = VectorStoreWrapper(vector_store) if vector_store else None
        self.vector_store_filter = vector_store_filter
        self.websocket = websocket
        self.agent = agent
        self.role = role
        self.parent_query = parent_query
        self.subtopics = subtopics
        self.visited_urls = visited_urls
        self.verbose = verbose
        self.context = context
        self.headers = headers or {}
        self.retrievers = get_retrievers(self.headers, self.cfg)
        self.memory = Memory(
            self.cfg.embedding_provider, self.cfg.embedding_model, **self.cfg.embedding_kwargs
        )
        self.sub_queries = []
        self.scrape_data = {}
        self.content = {}
        self.history = {}
        self.task_id = task_id
        self.is_deep = is_deep
        # Initialize components
        self.research_conductor: ResearchConductor = ResearchConductor(self)
        self.report_generator: ReportGenerator = ReportGenerator(self)
        self.context_manager: ContextManager = ContextManager(self)
        self.scraper_manager: BrowserManager = BrowserManager(self)
        self.dialogue_service: DialogueService = DialogueService()
        self.source_curator: SourceCurator = SourceCurator(self)
        self.deep_researcher: Optional[DeepResearchSkill] = None
        if report_type == ReportType.DeepResearch.value:
            self.deep_researcher = DeepResearchSkill(self)
    async def conduct_research(self, on_progress=None):
        if self.report_type == ReportType.DeepResearch.value and self.deep_researcher:
            #lgq测试
            # self.deep_researcher.depth = 1
            # self.deep_researcher.breadth = 1
            return await self._handle_deep_research(on_progress)
        if not (self.agent and self.role):
            self.agent = "舆情信息检索代理"
            self.role = "你是一位专业的舆情分析AI助手，负责基于给定问题和上下文，检索并提取、整理并总结关键信息。你的任务是准确分析事件背景、传播动态、公众情绪和潜在影响，以结构化方式呈现，确保内容中立、全面且清晰。"
        self.context = await self.research_conductor.conduct_research()
        return self.context

    async def _handle_deep_research(self, on_progress=None):
        """Handle deep research execution and logging."""
        # Log deep research configuration
        # await self._log_event("research", step="deep_research_initialize", details={
        #     "type": "deep_research",
        #     "breadth": self.deep_researcher.breadth,
        #     "depth": self.deep_researcher.depth,
        #     "concurrency": self.deep_researcher.concurrency_limit
        # })

        # Run deep research and get context
        self.context = await self.deep_researcher.run(on_progress=on_progress)

        return self.context

    async def write_report(self, existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        return await self.report_generator.write_report(
            existing_headers,
            relevant_written_contents,
            ext_context or self.context
        )

    async def write_report_by_type(self, report_type: str,existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        return await self.report_generator.write_report_by_type(
            report_type,
            existing_headers,
            relevant_written_contents,
            ext_context or self.context
        )
    async def write_report_conclusion(self, report_body: str) -> str:
        return await self.report_generator.write_report_conclusion(report_body)

    async def write_introduction(self):
        return await self.report_generator.write_introduction()

    async def get_subtopics(self):
        return await self.report_generator.get_subtopics()

    async def get_draft_section_titles(self, current_subtopic: str):
        return await self.report_generator.get_draft_section_titles(current_subtopic)

    async def get_similar_written_contents_by_draft_section_titles(
        self,
        current_subtopic: str,
        draft_section_titles: List[str],
        written_contents: List[Dict],
        max_results: int = 10
    ) -> List[str]:
        return await self.context_manager.get_similar_written_contents_by_draft_section_titles(
            current_subtopic,
            draft_section_titles,
            written_contents,
            max_results
        )

    # Utility methods
    def get_research_images(self, top_k=10) -> List[Dict[str, Any]]:
        return self.research_images[:top_k]

    def add_research_images(self, images: List[Dict[str, Any]]) -> None:
        self.research_images.extend(images)

    def get_research_sources(self) -> List[Dict[str, Any]]:
        return self.research_sources

    def add_research_sources(self, sources: List[Dict[str, Any]]) -> None:
        self.research_sources.extend(sources)

    def add_references(self, report_markdown: str, visited_urls: set) -> str:
        return add_references(report_markdown, visited_urls)

    def extract_headers(self, markdown_text: str) -> List[Dict]:
        return extract_headers(markdown_text)

    def extract_sections(self, markdown_text: str) -> List[Dict]:
        return extract_sections(markdown_text)

    def table_of_contents(self, markdown_text: str) -> str:
        return table_of_contents(markdown_text)

    def get_source_urls(self) -> list:
        return list(self.visited_urls)

    def get_research_context(self) -> list:
        return self.context

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

