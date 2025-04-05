from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

# 数据库连接字符串
DATABASE_URL = "mysql+mysqlconnector://root:111111@localhost/graduation"

# 创建 SQLAlchemy 引擎
engine = create_engine(DATABASE_URL, echo=True)

# 基础类
Base = declarative_base()

# 定义模型
class Dialogue(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False)  # task_id 使用字符串（UUID）格式
    original_question = Column(Text, nullable=False)  # 原始问题
    subqueries = Column(Text, nullable=False)  # 子问题
    search_data = Column(JSON, default=None)  # 存储搜索结果的 JSON 字段
    conversations = Column(JSON, default=None)  # 存储对话信息的 JSON 字段
    created_at = Column(TIMESTAMP, default=datetime.utcnow)  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 工具类，封装数据库操作
class Database:
    def __init__(self):
        self.session = None

    def get_session(self):
        if self.session is None:
            self.session = SessionLocal()
        return self.session

    def close_session(self):
        if self.session:
            self.session.close()
            self.session = None

    def create_dialogue(self, original_question: str, subqueries: str, search_data: list, conversations: list):
        session = self.get_session()
        new_dialogue = Dialogue(
            task_id=str(uuid.uuid4()),  # 生成任务ID
            original_question=original_question,
            subqueries=subqueries,
            search_data=search_data,
            conversations=conversations
        )
        session.add(new_dialogue)
        session.commit()

    def get_dialogue(self, dialogue_id: int):
        session = self.get_session()
        dialogue = session.query(Dialogue).filter(Dialogue.id == dialogue_id).first()
        return dialogue

    def update_dialogue(self, dialogue_id: int, new_data: dict):
        session = self.get_session()
        dialogue = session.query(Dialogue).filter(Dialogue.id == dialogue_id).first()
        if dialogue:
            for key, value in new_data.items():
                setattr(dialogue, key, value)
            session.commit()

# 创建表（如果还没有创建）
Base.metadata.create_all(engine)

