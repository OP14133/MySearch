import asyncio
from datetime import datetime, timedelta
import logging
import re
import uuid
from typing import Dict, List, Union, Tuple
from MySearch.search.service.DialogueService import DialogueService
from fastapi import WebSocket
from MySearch.backend.report_type import BasicReport, DetailedReport
from MySearch.backend.chat import ChatAgentWithMemory
from MySearch.search.utils.enum import ReportType, Tone
from MySearch.search.agent import GPTResearcher

from MySearch.backend.report_type.deep_research.deep_report import DeepReport


# from multi_agents.main import run_research_task
from MySearch.search.actions import stream_output  # Import stream_output
from langchain_chroma import Chroma

from MySearch.search.config import Config
from MySearch.search.memory import Memory

from MySearch.search.actions.query_processing import get_search_results
from MySearch.search.utils.llm import create_chat_completion

from MySearch.search.actions import get_retrievers


class WebSocketManager:
    """Manage websockets"""

    def __init__(self):
        """初始化WebSocketManager 类."""
        self.active_connections: List[WebSocket] = []  #存储当前活动的WebSocket
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {} #存储每个WebSocket的发送任务
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {} #存储每个WebSocket的消息队列
        self.chat_agents: Dict[WebSocket, ChatAgentWithMemory] = {}
        self.task_id: Dict[WebSocket, str]
        # self.researchers: Dict[WebSocket, Union[BasicReport,DetailedReport]] = {}

    async def start_sender(self, websocket: WebSocket):
        """方法用于启动一个发送任务，该任务会从消息队列中获取消息并发送到指定的 WebSocket"""
        queue = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except:
                    break
            else:
                break

    async def connect(self, websocket: WebSocket):
        """接受一个新的 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        #创建一个发送任务
        self.sender_tasks[websocket] = asyncio.create_task(
            self.start_sender(websocket))

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.sender_tasks[websocket].cancel()
            await self.message_queues[websocket].put(None)
            del self.sender_tasks[websocket]
            del self.message_queues[websocket]


    async def start_streaming(self, task, report_type, report_source, source_urls, tone, websocket, task_id, headers=None):
        """Start streaming the output."""
        tone = Tone["Objective"]
        if report_type is None:
            report_type = ReportType.SummeryReport  # 默认报告类型
        if report_source is None:
            report_source = "web"  # 默认报告来源
        if source_urls is None:
            source_urls = []  # 默认来源 URL 列表
        cfg = Config()
        memory = Memory(cfg.embedding_provider, cfg.embedding_model, **cfg.embedding_kwargs)
        embeddings = memory.get_embeddings()
        vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        report, researcher = await run_agent(task, report_type, report_source, source_urls, tone, websocket, task_id=task_id, vector_store=vector_store, headers=headers)
#         await websocket.send_json({"type": "report", "output": report})
        #Create new Chat Agent whenever a new report is written
        documents = str(researcher.sub_queries) + str(researcher.context) + report
        chat_agent = ChatAgentWithMemory(report=documents, headers=headers,websocket=websocket, vector_store=vector_store)
        self.chat_agents[websocket] = chat_agent
        # self.researchers[websocket] = researcher
        return report

    async def chat(self, message, websocket):
        """基于消息差异与代理进行聊天"""
        if self.chat_agents:
            # subtopics = self.researchers[websocket].subtopics
            await self.chat_agents[websocket].chat(message, websocket)
        else:
            try:
                await websocket.send_json({"type": "chat", "output": "知识库为空，请先运行研究以获取知识"})
                await websocket.send_json({"type": "chat_finish", "output": "知识库为空，请先运行研究以获取知识"})
            except Exception as e:
                logging.error(f"通过 WebSocket 发送 JSON 时出错: {e}")
async def run_agent(task, report_type, report_source, source_urls, tone: Tone, websocket, task_id, vector_store=None, headers=None, config_path=""):
    """Run the agent."""
    start_time = datetime.now()
    # Instead of running the agent directly run it through the different report type classes
    keywords, start_ts, end_ts = await extract_keywords_and_date_range(task)
    content = f"关键词: {keywords}\n时间范围: {start_ts} ~ {end_ts}"
    output = {
        "keywords": keywords,
        "start_time": start_ts,
        "end_time": end_ts
    }
    await stream_output(
        type="keyword_range",  # 也可以换成自定义类型，比如 "keyword_range"
        content="已提取关键词与时间范围",
        output=content,
        websocket=websocket,
        metadata=output  # 结构化数据可供前端使用
    )

    if report_type == ReportType.DetailedReport.value:
        researcher = DetailedReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            tone=tone,
            config_path=config_path,
            websocket=websocket,
            headers=headers,
        )
        report = await researcher.run()

    elif report_type == ReportType.DeepResearch.value:
        print("---------走到了深度搜索")
        researcher = DeepReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            tone=tone,
            config_path=config_path,
            websocket=websocket,
            headers=headers,
            sub_queries=None,
            context=None,
            task_id=task_id,
            vector_store=vector_store
        )
        report = await researcher.run()
    else:
        print("---------走到了基础搜索")
        researcher = BasicReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            tone=tone,
            config_path=config_path,
            websocket=websocket,
            headers=headers,
            sub_queries=None,
            context=None,
            task_id=task_id,
            vector_store=vector_store
        )
        report = await researcher.run()
    # measure time
    end_time = datetime.now()
    await websocket.send_json(
        {"type": "logs", "output": f"\n检索耗时: {end_time - start_time}\n"}
    )

    return report, researcher


async def extract_keywords_and_date_range(query: str) -> Tuple[str, str, str]:
    """
    根据查询和搜索结果，生成适用于社交媒体搜索的关键词和事件时间范围。

    返回:
        keywords: 用于搜索的关键词表达式 (如: "香菇 OR 金针菇 OR (蘑菇 AND 美食)")
        start_timestamp: 起始时间戳 (字符串格式)
        end_timestamp: 结束时间戳 (字符串格式)
    """
    try:
        cfg = Config()
        retrievers = get_retrievers({}, cfg)
        # Step 1: 获取搜索结果
        search_results = await get_search_results(query, retrievers[0])
        # logger.info(f"已获取初始搜索结果，共 {len(search_results)} 条")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Step 2: 构造 prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位信息提取专家，擅长从新闻摘要中提取关键词与事件时间范围。"
                    "用户希望通过关键词和时间段在社交媒体中进一步检索相关新闻和讨论。"
                )
            },
            {
                "role": "user",
                "content": f"""原始查询: {query}

当前时间: {current_time}

搜索结果:
{search_results}

请根据搜索结果完成以下任务：
1. 提取用于社交媒体搜索的关键词逻辑表达式，尽可能覆盖不同表达方式（如同义词、缩写等），表达式中使用 AND / OR 连接，例如："香菇 OR 金针菇 OR (蘑菇 AND 美食)"。
2. 分析事件发生的时间范围，返回一个标准化格式："YYYY-MM-DD ~ YYYY-MM-DD"，用于作为检索时间窗口，注意时间范围不超过7天，并且必须是近一年之内的数据，选择该事件最关键的事件节点范围。

最终请严格按照如下格式输出：
keywords: xxx
date: yyyy-mm-dd ~ yyyy-mm-dd
- “keywords:” 和 “date:” 两行必须各自独占一行，不能拆分或省略。
- 格式必须严格符合，否则无法被识别。
"""
            }
        ]

        # Step 3: 调用大模型
        response = await create_chat_completion(
            model=cfg.strategic_model,
            messages=messages,
            temperature=0.3,
            llm_kwargs=cfg.llm_kwargs,
        )
        logger = logging.getLogger(__name__)

        # Step 4: 解析大模型返回
        keyword_line = ""
        date_line = ""
        start_timestamp = ""
        end_timestamp = ""

        # 提取关键词
        keywords_match = re.search(r"keywords:\s*(.+)", response, re.IGNORECASE)
        if keywords_match:
            keyword_line = keywords_match.group(1).strip()

        # 提取日期范围
        date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", response)
        if date_match:
            start_str, end_str = date_match.group(1), date_match.group(2)
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                start_timestamp = str(int(start_dt.timestamp()))
                end_timestamp = str(int(end_dt.timestamp()))
            except Exception as e:
                logger.warning(f"时间格式解析失败: {e}")

        # Step 5: 如果任何字段缺失，则使用默认值
        if not keyword_line:
            logger.warning("关键词提取失败，使用原始 query 作为 fallback")
            keyword_line = query

        if not start_timestamp or not end_timestamp:
            logger.warning("时间范围提取失败，使用默认时间范围（近三天）")
            fallback_start = datetime.now() - timedelta(days=3)
            fallback_end = datetime.now()
            start_timestamp = str(int(fallback_start.timestamp()))
            end_timestamp = str(int(fallback_end.timestamp()))

        return keyword_line, start_timestamp, end_timestamp

    except Exception as e:
        logger.error(f"提取关键词与时间范围失败，使用默认值。错误详情: {e}")
        fallback_start = datetime.now() - timedelta(days=3)
        fallback_end = datetime.now()
        return query, str(int(fallback_start.timestamp())), str(int(fallback_end.timestamp()))