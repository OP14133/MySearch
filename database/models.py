from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, TIMESTAMP
from sqlalchemy.dialects.mysql import LONGTEXT

from database import Base
from datetime import datetime, timezone

class Dialogue(Base):
    __tablename__ = 'dialogues'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False)  # task_id 使用字符串（UUID）格式，添加唯一索引
    original_question = Column(Text, nullable=False)  # 原始问题
    subqueries = Column(JSON, default=list, nullable=True)  # 子问题，保存为字符串列表
    urls = Column(JSON, default=list, nullable=True)  # 存储URLs列表
    conversations = Column(JSON, default=None, nullable=True)  # 存储对话信息的 JSON 字段
    summery = Column(Text, nullable=True)
    timeline = Column(JSON, default=list, nullable=True)  # 新增时间线列，存储JSON格式的时间线列表

    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))  # 创建时间
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))  # 更新时间


class WebPageDetails(Base):
    __tablename__ = 'web_page_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, unique=True)
    url = Column(String(512), unique=True, nullable=False)  # URL，保证唯一性
    title = Column(String(255), nullable=True)  # 网页标题
    body = Column(Text, nullable=True)  # 网页正文内容
    content = Column(LONGTEXT, nullable=True)  # 网页内容
    image_urls = Column(JSON, default=list)  # 存储图像 URL 列表

