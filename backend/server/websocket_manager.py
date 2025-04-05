import asyncio
import datetime
import uuid
from typing import Dict, List, Union
from MySearch.search.service.DialogueService import DialogueService
from fastapi import WebSocket
from MySearch.backend.report_type import BasicReport, DetailedReport
from MySearch.backend.chat import ChatAgentWithMemory
from MySearch.search.utils.enum import ReportType, Tone
from MySearch.search.agent import GPTResearcher

from MySearch.backend.report_type.deep_research.deep_report import DeepReport


# from multi_agents.main import run_research_task
# from gpt_researcher.actions import stream_output  # Import stream_output


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
        report, researcher = await run_agent(task, report_type, report_source, source_urls, tone, websocket, task_id = task_id, headers=headers)
#         await websocket.send_json({"type": "report", "output": report})
        #Create new Chat Agent whenever a new report is written
        documents = str(researcher.sub_queries) + str(researcher.context) + report
        chat_agent = ChatAgentWithMemory(report=documents, headers=headers,websocket=websocket)
        self.chat_agents[websocket] = chat_agent
        # self.researchers[websocket] = researcher
        return report

    async def chat(self, message, websocket):
        """基于消息差异与代理进行聊天"""
        # chat_agent = ChatAgentWithMemory(message,headers)
        if self.chat_agents:
            # subtopics = self.researchers[websocket].subtopics
            await self.chat_agents[websocket].chat(message, websocket)
        else:
            await websocket.send_json({"type": "logs", "content": "知识库为空，请先运行研究以获取知识"})

async def run_agent(task, report_type, report_source, source_urls, tone: Tone, websocket, task_id, headers=None, config_path=""):
    """Run the agent."""
    start_time = datetime.datetime.now()
    # Instead of running the agent directly run it through the different report type classes
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
            task_id=task_id
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
            task_id=task_id
        )
        report = await researcher.run()
    # measure time
    end_time = datetime.datetime.now()
    await websocket.send_json(
        {"type": "logs", "output": f"\nTotal run time: {end_time - start_time}\n"}
    )

    return report, researcher
