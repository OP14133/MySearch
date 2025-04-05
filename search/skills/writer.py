from typing import Dict, Optional
import json

from ..utils.enum import ReportType
from ..utils.llm import construct_subtopics
from ..actions import (
    stream_output,
    generate_report,
    generate_draft_section_titles,
    write_report_introduction,
    write_conclusion
)


class ReportGenerator:
    """Generates reports based on research data."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.research_params = {
            "query": self.researcher.query,
            "agent_role_prompt": self.researcher.cfg.agent_role or self.researcher.role,
            "report_type": self.researcher.report_type,
            "report_source": self.researcher.report_source,
            "tone": self.researcher.tone,
            "websocket": self.researcher.websocket,
            "cfg": self.researcher.cfg,
            "headers": self.researcher.headers,
        }

    async def write_report(self, existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        """
        根据现有的标题和相关内容生成报告

        Args:
            existing_headers (list): 现有标题列表。
            relevant_written_contents (list): 相关已写内容列表。
            ext_context (Optional): 外部上下文（如果有）。

        Returns:
            str: 生成的报告。
        """
        # send the selected images prior to writing report
        # research_images = self.researcher.get_research_images()
        # if research_images:
        #     await stream_output(
        #         "images",
        #         "selected_images",
        #         json.dumps(research_images),
        #         self.researcher.websocket,
        #         True,
        #         research_images
        #     )

        context = ext_context or self.researcher.context
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_report",
                f"为 '{self.researcher.query}' 撰写报告...",
                self.researcher.websocket,
            )

        report_params = self.research_params.copy()
        report_params["context"] = context

        if self.researcher.report_type == "subtopic_report":
            report_params.update({
                "main_topic": self.researcher.parent_query,
                "existing_headers": existing_headers,
                "relevant_written_contents": relevant_written_contents,
            })

        report = await generate_report(**report_params)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "report_written",
                f"为 '{self.researcher.query}撰写报告'",
                self.researcher.websocket,
            )

        return report


    async def write_report_by_type(self, report_type,existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        """
        根据现有的标题和相关内容生成报告

        Args:
            existing_headers (list): 现有标题列表。
            relevant_written_contents (list): 相关已写内容列表。
            ext_context (Optional): 外部上下文（如果有）。

        Returns:
            str: 生成的报告。
        """
        context = ext_context or self.researcher.context
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_report",
                f"为 '{self.researcher.query}' 撰写报告...",
                self.researcher.websocket,
            )

        report_params = self.research_params.copy()
        report_params["context"] = context
        report_params["report_type"] = report_type

        report = await generate_report(**report_params)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "report_written",
                f"为 '{self.researcher.query}撰写报告'",
                self.researcher.websocket,
            )

        return report


    async def write_summery(self, existing_headers: list = [], relevant_written_contents: list = [], ext_context=None) -> str:
        """
        根据现有的标题和相关内容生成报告

        Args:
            existing_headers (list): 现有标题列表。
            relevant_written_contents (list): 相关已写内容列表。
            ext_context (Optional): 外部上下文（如果有）。

        Returns:
            str: 生成的报告。
        """
        context = ext_context or self.researcher.context
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_report",
                f"为 '{self.researcher.query}' 撰写事件概述...",
                self.researcher.websocket,
            )

        report_params = self.research_params.copy()
        report_params["context"] = context

        report = await generate_report(**report_params)
        return report
    async def write_report_conclusion(self, report_content: str) -> str:
        """
        Write the conclusion for the report.

        Args:
            report_content (str): The content of the report.

        Returns:
            str: The generated conclusion.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_conclusion",
                f"为 '{self.researcher.query}'撰写结论...",
                self.researcher.websocket,
            )

        conclusion = await write_conclusion(
            query=self.researcher.query,
            context=report_content,
            config=self.researcher.cfg,
            agent_role_prompt=self.researcher.cfg.agent_role or self.researcher.role,
            websocket=self.researcher.websocket,
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "conclusion_written",
                f"为 '{self.researcher.query}'撰写结论",
                self.researcher.websocket,
            )

        return conclusion

    async def write_introduction(self):
        """Write the introduction section of the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "writing_introduction",
                f"为 '{self.researcher.query}'撰写引言...",
                self.researcher.websocket,
            )

        introduction = await write_report_introduction(
            query=self.researcher.query,
            context=self.researcher.context,
            agent_role_prompt=self.researcher.cfg.agent_role or self.researcher.role,
            config=self.researcher.cfg,
            websocket=self.researcher.websocket,
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "introduction_written",
                f"为 '{self.researcher.query}'撰写引言",
                self.researcher.websocket,
            )

        return introduction

    async def get_subtopics(self):
        """Retrieve subtopics for the research."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_subtopics",
                f"正在生成 '{self.researcher.query}' 的子主题...",
                self.researcher.websocket,
            )

        subtopics = await construct_subtopics(
            task=self.researcher.query,
            data=self.researcher.context,
            config=self.researcher.cfg,
            subtopics=self.researcher.subtopics,
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "subtopics_generated",
                f"正在生成 '{self.researcher.query}' 的子主题",
                self.researcher.websocket,
            )

        return subtopics

    async def get_draft_section_titles(self, current_subtopic: str):
        """Generate draft section titles for the report."""
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "generating_draft_sections",
                f"正在为 '{self.researcher.query}' 生成草稿部分标题...",
                self.researcher.websocket,
            )

        draft_section_titles = await generate_draft_section_titles(
            query=self.researcher.query,
            current_subtopic=current_subtopic,
            context=self.researcher.context,
            role=self.researcher.cfg.agent_role or self.researcher.role,
            websocket=self.researcher.websocket,
            config=self.researcher.cfg,
        )

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "draft_sections_generated",
                f"为 '{self.researcher.query}' 生成的草稿部分标题",
                self.researcher.websocket,
            )

        return draft_section_titles
