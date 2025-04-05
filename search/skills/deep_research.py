from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import datetime, timedelta
# from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from search.utils.llm import create_chat_completion
from search.utils.enum import ReportType, ReportSource, Tone
from search.actions.query_processing import get_search_results
from MySearch.search.actions import stream_output

logger = logging.getLogger(__name__)

# Maximum words allowed in context (25k words for safety margin)
MAX_CONTEXT_WORDS = 25000

def count_words(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())

def trim_context_to_word_limit(context_list: List[str], max_words: int = MAX_CONTEXT_WORDS) -> List[str]:
    """Trim context list to stay within word limit while preserving most recent/relevant items"""
    total_words = 0
    trimmed_context = []

    # Process in reverse to keep most recent items
    for item in reversed(context_list):
        words = count_words(item)
        if total_words + words <= max_words:
            trimmed_context.insert(0, item)  # Insert at start to maintain original order
            total_words += words
        else:
            break

    return trimmed_context

class ResearchProgress:
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = 1  # Start from 1 and increment up to total_depth
        self.total_depth = total_depth
        self.current_breadth = 0  # Start from 0 and count up to total_breadth as queries complete
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0


class DeepResearchSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.breadth = getattr(researcher.cfg, 'deep_research_breadth', 5)
        self.depth = getattr(researcher.cfg, 'deep_research_depth', 2)
        self.concurrency_limit = getattr(researcher.cfg, 'deep_research_concurrency', 5)
        self.websocket = researcher.websocket
        self.tone = researcher.tone
        self.config_path = researcher.cfg.config_path if hasattr(researcher.cfg, 'config_path') else None
        self.headers = researcher.headers or {}
        self.visited_urls = researcher.visited_urls
        self.learnings = []
        self.research_sources = []  # Track all research sources
        self.context = []  # Track all context

    async def generate_search_queries(self, query: str, num_queries: int = 5) -> List[Dict[str, str]]:
        """生成用于研究的 SERP 查询"""
        messages = [
            {"role": "system", "content": "你是一位专家级研究员，负责生成搜索查询。"},
            {"role": "user",
             "content": f"根据以下提示，生成 {num_queries} 个独特的搜索查询，以全面研究该主题。"
                        f"对于每个查询，请提供一个研究目标。"
                        f"格式如下：'Query: <query>'，然后是 'Goal: <goal>'，每对一行：{query}"}
        ]

        response = await create_chat_completion(
            model=self.researcher.cfg.strategic_model,
            messages=messages,
            temperature=0.4,
            max_tokens=None,
            llm_kwargs=self.researcher.cfg.llm_kwargs,
        )

        lines = response.split('\n')
        queries = []
        current_query = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Query:'):
                if current_query:
                    queries.append(current_query)
                current_query = {'query': line.replace('Query:', '').strip()}
            elif line.startswith('Goal:') and current_query:
                current_query['researchGoal'] = line.replace('Goal:', '').strip()

        if current_query:
            queries.append(current_query)

        return queries[:num_queries]

    async def generate_research_plan(self, query: str, num_questions: int = 5) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        # Get initial mysearch results to inform query generation
        search_results = await get_search_results(query, self.researcher.retrievers[0])
        logger.info(f"已获取初始网络知识：{len(search_results)}条结果")

        # Get current time for context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        messages = [
            {"role": "system", "content": "你是一名专业研究员，专注于舆情事件分析。你的任务是分析原始查询和搜索结果，并生成研究问题，以便全面解析该事件的演变过程和影响。"},
            {"role": "user",
             "content": f"""原始查询: {query}

当前时间: {current_time}

搜索结果:
{search_results}

根据这些结果、原始查询和当前时间，生成{num_questions}个独特的问题。参考以下五个方面：
1. 事件详情：背景、起因、关键时间节点、涉及的主要人物或组织。
2. 最新动态：最近发生的更新或重要声明，包括相关方的新举措或影响。
3. 社会反应与公众情绪：民众的讨论、社交媒体趋势、情感倾向分析。
4. 后续影响：事件对社会、经济、政治等方面的潜在或已知影响。
5. 时间线发展：从事件起始到当前的完整发展脉络。

每个问题请以'Question: '开头并单独成行"""}
        ]

        response = await create_chat_completion(
            model=self.researcher.cfg.strategic_model,
            messages=messages,
            temperature=0.4,
            llm_kwargs=self.researcher.cfg.llm_kwargs,
        )

        questions = [q.replace('Question:', '').strip()
                     for q in response.split('\n')
                     if q.strip().startswith('Question:')]
        return questions[:num_questions]

    async def process_research_results(self, query: str, context: str, num_learnings: int = 3) -> Dict[str, List[str]]:
        """处理调研结果，以提取关键发现和后续问题"""
        messages = [
            {"role": "system", "content": "You are an expert researcher analyzing search results."},
            {"role": "user",
             "content": f"Given the following research results for the query '{query}', extract key learnings and suggest follow-up questions. For each learning, include a citation to the source URL if available. Format each learning as 'Learning [source_url]: <insight>' and each question as 'Question: <question>':\n\n{context}"}
        ]

        response = await create_chat_completion(
            model=self.researcher.cfg.strategic_model,
            messages=messages,
            temperature=0.4,
            max_tokens=1000,
            llm_kwargs=self.researcher.cfg.llm_kwargs,
        )

        lines = response.split('\n')
        learnings = []
        questions = []
        citations = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Learning'):
                import re
                url_match = re.search(r'\[(.*?)\]:', line)
                if url_match:
                    url = url_match.group(1)
                    learning = line.split(':', 1)[1].strip()
                    learnings.append(learning)
                    citations[learning] = url
                else:
                    # Try to find URL in the line itself
                    url_match = re.search(
                        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                    if url_match:
                        url = url_match.group(0)
                        learning = line.replace(url, '').replace('Learning:', '').strip()
                        learnings.append(learning)
                        citations[learning] = url
                    else:
                        learnings.append(line.replace('Learning:', '').strip())
            elif line.startswith('Question:'):
                questions.append(line.replace('Question:', '').strip())

        return {
            'learnings': learnings[:num_learnings],
            'followUpQuestions': questions[:num_learnings],
            'citations': citations
        }

    async def deep_research(
            self,
            query: str,
            breadth: int,
            depth: int,
            learnings: List[str] = None,
            citations: Dict[str, str] = None,
            visited_urls: Set[str] = None,
            on_progress=None
    ) -> Dict[str, Any]:
        """Conduct deep iterative research"""
        if learnings is None:
            learnings = []
        if citations is None:
            citations = {}
        if visited_urls is None:
            visited_urls = set()

        progress = ResearchProgress(depth, breadth)

        if on_progress:
            on_progress(progress)

        # Generate mysearch queries
        serp_queries = await self.generate_search_queries(query, num_queries=breadth)
        """
        子问题 ，目前设置为了1
        [{'query': '2022年俄乌冲突的背景、演变过程及关键转折点', 'researchGoal': '研究2022年俄乌冲突的起因、发展过程以及导致战争全面爆发的关键事件和时间节点。'}]
        """
        progress.total_queries = len(serp_queries)

        all_learnings = learnings.copy()
        all_citations = citations.copy()
        all_visited_urls = visited_urls.copy()
        all_context = []
        all_sources = []

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: Dict[str, str]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    progress.current_query = serp_query['query']
                    if on_progress:
                        on_progress(progress)

                    # from .. import GPTResearcherR
                    from ..agent import GPTResearcher
                    from ..memory import Memory
                    from langchain_chroma import Chroma
                    memory = Memory(self.researcher.cfg.embedding_provider, self.researcher.cfg.embedding_model, **self.researcher.cfg.embedding_kwargs)
                    embeddings = memory.get_embeddings()
                    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

                    # self.breadth = 1
                    # self.depth = 1
                    researcher = GPTResearcher(
                        query=serp_query['query'],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        headers=self.headers,
                        visited_urls=self.visited_urls,
                        # vector_store=vector_store
                        vector_store=self.researcher.vector_store
                    )

                    # Conduct research
                    context = await researcher.conduct_research()

                    # Get results and visited URLs
                    visited = researcher.visited_urls
                    sources = researcher.research_sources

                    # 根据返回的结果判断是否有新的问题，扩展查询Process results to extract learnings and citations
                    results = await self.process_research_results(
                        query=serp_query['query'],
                        context=context
                    )

                    # Update progress
                    progress.completed_queries += 1
                    progress.current_breadth += 1
                    if on_progress:
                        on_progress(progress)

                    return {
                        'learnings': results['learnings'],
                        'visited_urls': list(visited),
                        'followUpQuestions': results['followUpQuestions'],
                        'researchGoal': serp_query['researchGoal'],
                        'citations': results['citations'],
                        'context': context if context else "",
                        'sources': sources if sources else []
                    }

                except Exception as e:
                    logger.error(f"Error processing query '{serp_query['query']}': {str(e)}")
                    return None

        # Process queries concurrently with limit
        tasks = [process_query(query) for query in serp_queries]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]

        # Update breadth progress based on successful queries
        progress.current_breadth = len(results)
        if on_progress:
            on_progress(progress)

        # Collect all results
        for result in results:
            all_learnings.extend(result['learnings'])
            all_visited_urls.update(result['visited_urls'])
            all_citations.update(result['citations'])
            if result['context']:
                all_context.append(result['context'])
            if result['sources']:
                all_sources.extend(result['sources'])

            # Continue deeper if needed
            if depth > 1:
                new_breadth = max(2, breadth // 2)
                new_depth = depth - 1
                progress.current_depth += 1

                # Create next query from research goal and follow-up questions
                next_query = f"""
                Previous research goal: {result['researchGoal']}
                Follow-up questions: {' '.join(result['followUpQuestions'])}
                """

                # Recursive research
                deeper_results = await self.deep_research(
                    query=next_query,
                    breadth=new_breadth,
                    depth=new_depth,
                    learnings=all_learnings,
                    citations=all_citations,
                    visited_urls=all_visited_urls,
                    on_progress=on_progress
                )

                all_learnings = deeper_results['learnings']
                all_visited_urls.update(deeper_results['visited_urls'])
                all_citations.update(deeper_results['citations'])
                if deeper_results.get('context'):
                    all_context.extend(deeper_results['context'])
                if deeper_results.get('sources'):
                    all_sources.extend(deeper_results['sources'])

        # Update class tracking
        self.context.extend(all_context)
        self.research_sources.extend(all_sources)

        # Trim context to stay within word limits
        trimmed_context = trim_context_to_word_limit(all_context)
        logger.info(f"Trimmed context from {len(all_context)} items to {len(trimmed_context)} items to stay within word limit")

        return {
            'learnings': list(set(all_learnings)),
            'visited_urls': list(all_visited_urls),
            'citations': all_citations,
            'context': trimmed_context,
            'sources': all_sources
        }

    async def run(self, on_progress=None) -> str:
        """Run the deep research process and generate final report"""
        start_time = time.time()
        # Log initial costs
        # initial_costs = self.researcher.get_costs()
        follow_up_questions = await self.generate_research_plan(self.researcher.query)
        #follow_up_questions示例 字符串列表
        """
        ['2022年俄乌冲突的起因是什么，主要涉及哪些关键人物和组织，冲突爆发后经历了哪些重要的时间节点？', 
        '截至2025年4月，俄乌战争的最新动态是什么？双方在最近的军事行动中取得了哪些进展或遭遇了哪些挫折？', 
        '俄乌战争爆发以来，国际社会和民众对冲突的反应如何？社交媒体上关于俄乌战争的讨论趋势和情感倾向是怎样的？', 
        '俄乌战争对乌克兰和俄罗斯的经济、政治、社会等方面产生了哪些具体影响？国际社会对两国采取了哪些应对措施？', 
        '从2022年俄乌冲突爆发至今，俄乌战争的发展脉络是怎样的？冲突双方的力量对比发生了哪些变化，国际社会的立场和态度有何调整？']
        """
        #lgq这里有问题，没有发送到前端，self.websocket和self.researcher.websocket是同一个
        await stream_output(
            "plan",
            "research_plan",
            follow_up_questions,
            self.researcher.websocket,
        )
        answers = ["Automatically proceeding with research"] * len(follow_up_questions)
        qa_pairs = [f"Q: {q}\nA: {a}" for q, a in zip(follow_up_questions, answers)]
        combined_query = f"""
        Initial Query: {self.researcher.query}\nFollow - up Questions and Answers:\n
        """ + "\n".join(qa_pairs)
        logger.info(f"初始研究计划5个角度：\n{len(combined_query)}")
        results = await self.deep_research(
            query=combined_query,
            breadth=self.breadth,
            depth=self.depth,
            on_progress=on_progress
        )
        # Prepare context with citations
        context_with_citations = []
        for learning in results['learnings']:
            citation = results['citations'].get(learning, '')
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)

        # Add all research context
        if results.get('context'):
            context_with_citations.extend(results['context'])

        # Trim final context to word limit
        final_context = trim_context_to_word_limit(context_with_citations)
        
        # Set enhanced context and visited URLs
        self.researcher.context = "\n".join(final_context)
        self.researcher.visited_urls = results['visited_urls']

        # Set research sources
        if results.get('sources'):
            self.researcher.research_sources = results['sources']

        # Log total execution time
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        logger.info(f"Total research execution time: {execution_time}")
        # logger.info(f"Total research costs: ${research_costs:.2f}")

        # Return the context - don't generate report here as it will be done by the main agent
        return self.researcher.context