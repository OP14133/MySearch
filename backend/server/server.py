import json
import os
import sys
from pathlib import Path

import pandas as pd
import uvicorn
from qdata.baidu_index import PROVINCE_CODE

from MySearch.backend.server.social_media import fetch_news, fetch_data_from_api

from MySearch.search.actions import stream_output

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, WebSocket, HTTPException, Query, WebSocketDisconnect, File, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from MySearch.search.service.DialogueService import DialogueService
from MySearch.backend.server.websocket_manager import WebSocketManager
from MySearch.backend.server.server_utils import (
    get_config_dict,
    update_environment_variables, handle_file_upload, handle_file_deletion, handle_websocket_communication
)
from MySearch.backend.server.baidu_index import get_index_data, get_province_data,validate_time_range, validate_area
# from langchain_community.vectorstores import InMemoryVectorStore
# from MySearch.search.vector_store.siliconflow_embedding import SiliconFlowEmbeddings
# from langchain.retrievers.document_compressors import EmbeddingsFilter
# # Models


class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str


class ConfigRequest(BaseModel):
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_API_KEY: str
    OPENAI_API_KEY: str
    DOC_PATH: str
    RETRIEVER: str
    GOOGLE_API_KEY: str = ''
    GOOGLE_CX_KEY: str = ''
    BING_API_KEY: str = ''
    SEARCHAPI_API_KEY: str = ''
    SERPAPI_API_KEY: str = ''
    SERPER_API_KEY: str = ''
    SEARX_URL: str = ''


# App initialization
app = FastAPI()

@app.get("/index/trend")
async def get_index_trend(
        keyword: str = Query(..., description="搜索关键词"),
        time_range: str = Query('7', description="时间范围：7/30/90/180/all"),
        area: str = Query('', description="地区代码，默认为空表示全国")
):
    """获取百度指数趋势数据"""
    try:
        # 验证时间范围和地区代码
        validate_time_range(time_range)
        area = validate_area(area)

        # 计算日期范围
        end_date = datetime.now()
        if time_range == 'all':
            start_date = end_date - timedelta(days=365 * 2)
        else:
            start_date = end_date - timedelta(days=int(time_range))

        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # 获取百度指数数据
        df = get_index_data(keyword, start_date_str, end_date_str, area)

        # 按type分组处理数据
        result = []
        for type_name in df['type'].unique():
            type_data = df[df['type'] == type_name]
            result.append({
                "type": type_name,
                "data": [{
                    "date": row['date'],
                    "index": row['index']
                } for _, row in type_data.iterrows()]
            })

        return {"message": "success", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/index/province")
async def get_province_index(
        keywords: List[str] = Query(..., description="搜索关键词列表"),
        start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
        end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
        population_adjusted: bool = Query(False, description="是否进行人口标准化"),
        max_workers: int = Query(2, description="最大并行工作线程数")
):
    """获取省级行政区百度指数数据（并行版本）"""
    try:
        # 验证日期格式
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        # 验证日期范围
        if start > end:
            raise HTTPException(
                status_code=422,
                detail="开始日期不能大于结束日期"
            )

        # 验证关键词列表
        if not keywords:
            raise HTTPException(
                status_code=422,
                detail="关键词列表不能为空"
            )

        # 格式化关键词列表
        keywords_list = [[k] for k in keywords]

        # 获取省级数据
        province_items = list(PROVINCE_CODE.items())
        data_all = pd.DataFrame()

        # 并行获取数据
        for province_item in province_items:
            data_stats = get_province_data(province_item, keywords_list, start_date, end_date)
            if data_stats is not None:
                data_all = pd.concat([data_all, data_stats], ignore_index=True)

        if data_all.empty:
            return {"message": "未找到数据", "data": []}

        # 如果需要人口标准化，可以在此添加逻辑

        result = data_all.to_dict(orient='records')
        return {"message": "success", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket manager
manager = WebSocketManager()
dialogueService = DialogueService()
# db = Database()
# Middleware处理跨域资源共享（CORS）。CORS 是一种安全机制，用于控制哪些域可以访问你的 API。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DOC_PATH = os.getenv("DOC_PATH", "./my-docs")

# Startup event


@app.on_event("startup")
def startup_event():
    os.makedirs("outputs", exist_ok=True)
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
    os.makedirs(DOC_PATH, exist_ok=True)

# Routes


# @app.get("/")
# async def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request, "report": None})


@app.get("/getConfig")
async def get_config(
    langchain_api_key: str = Header(None),
    openai_api_key: str = Header(None),
    tavily_api_key: str = Header(None),
    google_api_key: str = Header(None),
    google_cx_key: str = Header(None),
    bing_api_key: str = Header(None),
    searchapi_api_key: str = Header(None),
    serpapi_api_key: str = Header(None),
    serper_api_key: str = Header(None),
    searx_url: str = Header(None)
):
    return get_config_dict(
        langchain_api_key, openai_api_key, tavily_api_key,
        google_api_key, google_cx_key, bing_api_key,
        searchapi_api_key, serpapi_api_key, serper_api_key, searx_url
    )


@app.get("/files/")
async def list_files():
    files = os.listdir(DOC_PATH)
    print(f"Files in {DOC_PATH}: {files}")
    return {"files": files}

@app.post("/setConfig")
async def set_config(config: ConfigRequest):
    update_environment_variables(config.dict())
    return {"message": "Config updated successfully"}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    return await handle_file_upload(file, DOC_PATH)


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    return await handle_file_deletion(filename, DOC_PATH)

# @app.get("/news/search")
# def search_news(
#     keyword: str = Query(..., description="检索关键词"),
#     page: int = Query(1, ge=1),
#     size: int = Query(10, ge=1, le=100),
#     sources: Optional[List[str]] = Query(None),
#     sentiments: Optional[List[str]] = Query(None),
#     start_time: Optional[str] = Query(None, description="格式: YYYY-MM-DD HH:MM:SS"),
#     end_time: Optional[str] = Query(None, description="格式: YYYY-MM-DD HH:MM:SS")
# ):
#     """
#     舆情新闻检索接口
#     """
#     return fetch_news(
#         keyword=keyword,
#         page=page,
#         size=size,
#         sources=sources,
#         sentiments=sentiments,
#         start_time=start_time,
#         end_time=end_time
#     )
# 定义请求体模型
class SearchParams(BaseModel):
    keyword: str = Field(..., description="检索关键词")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, ge=1, le=100, description="每页数量")
    sources: Optional[List[str]] = Field(None, description="数据来源列表")
    sentiments: Optional[List[str]] = Field(None, description="情感类型列表")
    start_time: Optional[str] = Field(None, description="开始时间，格式: YYYY-MM-DD HH:MM:SS")
    end_time: Optional[str] = Field(None, description="结束时间，格式: YYYY-MM-DD HH:MM:SS")
@app.post("/news/search")
def search_news(
    search_params: SearchParams  # 使用 Pydantic 模型来验证请求体
):
    """
    舆情新闻检索接口
    """
    return fetch_news(
        keyword=search_params.keyword,
        page=search_params.page,
        size=search_params.size,
        sources=search_params.sources,
        sentiments=search_params.sentiments,
        start_time=search_params.start_time,
        end_time=search_params.end_time
    )



class NewsQueryRequest(BaseModel):
    keyword: str
    sources: Optional[List[str]] = None
    sentiments: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
@app.post("/news/total")
async def get_news_total(
req: NewsQueryRequest
):
    data = fetch_data_from_api(req.keyword, req.sources, req.sentiments, req.start_time, req.end_time)

    if data.get("code") == 200:
        return {"code": 200, "msg": "success", "data": data.get("data", {})}
    else:
        return {"code": data.get("code", 500), "msg": data.get("msg", "Error occurred"), "data": {}}
@app.get("/history")
async def get_history(
        page: int = Query(1, description="页码，从 1 开始", ge=1),  # 页码，默认值为 1
        page_size: int = Query(10, description="每页记录数", ge=1, le=100)  # 每页记录数，默认值为 10
):
    # 调用服务层获取分页数据
    dialogues, total = dialogueService.get_all_dialogues(page=page, page_size=page_size)

    # 返回分页结果
    return {
        "data": dialogues,
        "pagination": {
            "total": total,  # 总记录数
            "page": page,  # 当前页码
            "page_size": page_size,  # 每页记录数
            "total_pages": (total + page_size - 1) // page_size  # 总页数
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # output = {
    #     "keywords": "小米su7",
    #     "start_time": "1743935184",
    #     "end_time": "1744021584"
    # }
    # await stream_output(
    #     type="keyword_range",  # 也可以换成自定义类型，比如 "keyword_range"
    #     content="已提取关键词与时间范围",
    #     output="1111",
    #     websocket=websocket,
    #     metadata=output  # 结构化数据可供前端使用
    # )
    """
    从这个函数进入执行，
    """
    try:
        await handle_websocket_communication(websocket, manager)
    except WebSocketDisconnect:
        print("WebSocket 暂时断开（可能是网络问题），保持连接状态")
        # logger.warning("WebSocket 暂时断开（可能是网络问题），保持连接状态")
        # await manager.disconnect(websocket)
if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=True)