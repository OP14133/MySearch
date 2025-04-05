from typing import Dict, Optional, List
import json
from ..config.config import Config
from ..utils.llm import create_chat_completion
from ..prompts import curate_sources as rank_sources_prompt
from ..actions import stream_output


class SourceCurator:
    """根据源文献的相关性、可信度和可靠性对其进行排名和数据整理"""

    def __init__(self, researcher):
        self.researcher = researcher

    async def curate_sources(
        self,
        source_data: List,
        max_results: int = 10,
    ) -> List:
        """
        根据研究数据和预定的准则对来源进行排序和整理
        
        Args:
            query: 研究查询或任务
            source_data: 要排名的源文档列表
            max_results: 返回的最多源数量
            
        Returns:
            str: 排名后的源 URL 列表及其理由
        """
        # print(f"\n\nCurating {len(source_data)} sources: {source_data}")
        # if self.researcher.verbose:
        #     await stream_output(
        #         "logs",
        #         "research_plan",
        #         f"⚖️ Evaluating and curating sources by credibility and relevance...",
        #         self.researcher.websocket,
        #     )

        response = ""
        try:
            response = await create_chat_completion(
                model=self.researcher.cfg.smart_llm_model,
                messages=[
                    {"role": "system", "content": f"{self.researcher.role}"},
                    {"role": "user", "content": rank_sources_prompt(
                        self.researcher.query, source_data, max_results)},
                ],
                temperature=0.2,
                max_tokens=8000,
                llm_provider=self.researcher.cfg.smart_llm_provider,
                llm_kwargs=self.researcher.cfg.llm_kwargs,
            )

            curated_sources = json.loads(response)
            print(f"\n\nFinal Curated sources {len(source_data)} sources: {curated_sources}")

            if self.researcher.verbose:
                await stream_output(
                    "logs",
                    "research_plan",
                    f"🏅 Verified and ranked top {len(curated_sources)} most reliable sources",
                    self.researcher.websocket,
                )

            return curated_sources

        except Exception as e:
            print(f"Error in curate_sources from LLM response: {response}")
            if self.researcher.verbose:
                await stream_output(
                    "logs", 
                    "research_plan",
                    f"🚫 Source verification failed: {str(e)}",
                    self.researcher.websocket,
                )
            return source_data
