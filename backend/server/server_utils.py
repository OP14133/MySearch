import json
import os
import re
import time
import random
import shutil
import uuid
from typing import Dict, List, Any
from fastapi.responses import JSONResponse
from ...search.document.document import DocumentLoader
# Add this import
from ..utils import write_md_to_pdf, write_md_to_word, write_text_to_md


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()


def generate_unique_id():
    # 获取当前的时间戳（秒级）
    timestamp = int(time.time())

    # 生成一个随机数，确保在同一时间戳内有足够的随机性
    random_part = random.randint(100000, 999999)

    # 合并时间戳和随机数，形成一个唯一的ID
    unique_id = f"{timestamp}{random_part}"

    return unique_id

async def handle_start_command(websocket, data, manager):
    print("data:",data)
    # json_data = json.loads(data)
    #解析 JSON 数据并返回
    task, report_type, source_urls, tone, headers, report_source = extract_command_data(
        data)

    if not task or not report_type:
        print("Error: Missing task or report_type")
        return
    #安全的文件名
    sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{task}")
    #启动报告生成流程，异步
    # mysql 插入task（用户问题）report_type（报告类型）
    task_id = generate_unique_id()
    report = await manager.start_streaming(
        task, report_type, report_source, source_urls, tone, websocket, task_id, headers
    )
    report = str(report)
    #生成报告文件
    file_paths = await generate_report_files(report, sanitized_filename)
    #发送websocket到前端，生成报告的文件路径
    await send_file_paths(websocket, file_paths)


async def handle_human_feedback(data: str):
    feedback_data = json.loads(data[14:])  # Remove "human_feedback" prefix
    print(f"Received human feedback: {feedback_data}")
    # TODO: Add logic to forward the feedback to the appropriate agent or update the research state

async def handle_chat(websocket, data, manager):
    # json_data = json.loads(data)
    print(f"Received chat message: {data.get('context')}")#message是用户第二轮提问
    await manager.chat(data.get("context"), websocket)

async def generate_report_files(report: str, filename: str) -> Dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {"pdf": pdf_path, "docx": docx_path, "md": md_path}


async def send_file_paths(websocket, file_paths: Dict[str, str]):
    await websocket.send_json({"type": "path", "output": file_paths})


def get_config_dict(
    langchain_api_key: str, openai_api_key: str, tavily_api_key: str,
    google_api_key: str, google_cx_key: str, bing_api_key: str,
    searchapi_api_key: str, serpapi_api_key: str, serper_api_key: str, searx_url: str
) -> Dict[str, str]:
    return {
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
        "TAVILY_API_KEY": tavily_api_key or os.getenv("TAVILY_API_KEY", ""),
        "GOOGLE_API_KEY": google_api_key or os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key or os.getenv("GOOGLE_CX_KEY", ""),
        "BING_API_KEY": bing_api_key or os.getenv("BING_API_KEY", ""),
        "SEARCHAPI_API_KEY": searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", ""),
        "SERPAPI_API_KEY": serpapi_api_key or os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key or os.getenv("SERPER_API_KEY", ""),
        "SEARX_URL": searx_url or os.getenv("SEARX_URL", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "DOC_PATH": os.getenv("DOC_PATH", "./my-docs"),
        "RETRIEVER": os.getenv("RETRIEVER", ""),
        "EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", "")
    }


def update_environment_variables(config: Dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value


async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"File uploaded to {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": file.filename, "path": file_path}


async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    file_path = os.path.join(DOC_PATH, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File deleted: {file_path}")
        return JSONResponse(content={"message": "File deleted successfully"})
    else:
        print(f"File not found: {file_path}")
        return JSONResponse(status_code=404, content={"message": "File not found"})


# async def execute_multi_agents(manager) -> Any:
#     websocket = manager.active_connections[0] if manager.active_connections else None
#     if websocket:
#         # report = await run_research_task("Is AI in a hype cycle?", websocket, stream_output)
#         return {"report": report}
#     else:
#         return JSONResponse(status_code=400, content={"message": "No active WebSocket connection"})


async def handle_websocket_communication(websocket, manager):
    while True:
        data = await websocket.receive_text()#从 WebSocket 连接中接收文本消息，并将其存储在 data 变量中
        json_data = json.loads(data)
        data_type = json_data.get("type")
        if data_type == "start":
            # task_id = str(uuid.uuid4())
            await handle_start_command(websocket, json_data, manager)#从接收到的消息中提取必要的数据，并启动一个报告生成流程。最后，它将生成的文件路径发送回客户端。
        elif data_type == "chat":
            await handle_chat(websocket, json_data, manager)
        else:
            print("Error: Unknown command or not enough parameters provided.")


def extract_command_data(json_data: Dict) -> tuple:
    return (
        json_data.get("task"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("tone"),
        json_data.get("headers", {}),
        json_data.get("report_source")
    )
