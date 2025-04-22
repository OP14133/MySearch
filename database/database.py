from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, TIMESTAMP, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import relationship
from contextlib import contextmanager
from datetime import datetime
# 数据库连接字符串
DATABASE_URL = "mysql+mysqlconnector://root:111111@localhost/graduation"
# 基础类
Base = declarative_base()
class DatabaseManager:
    """数据库管理工具类"""

    def __init__(self):
        """初始化数据库管理器"""
        self.engine = create_engine(DATABASE_URL, echo=True)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine, autocommit=False, autoflush=False))

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self):
        """
        获取数据库会话
        使用 contextmanager 确保会话在操作后正确关闭
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()  # 提交事务
        except Exception as e:
            session.rollback()  # 出现异常回滚事务
            raise e
        finally:
            session.close()
# 定义模型
class Dialogue(Base):
    __tablename__ = 'dialogues'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, unique=True)  # task_id 使用字符串（UUID）格式，添加唯一索引
    original_question = Column(Text, nullable=False)  # 原始问题
    subqueries = Column(JSON, default=list, nullable=True)  # 子问题，保存为字符串列表
    urls = Column(JSON, default=list, nullable=True)  # 存储URLs列表
    conversations = Column(JSON, default=None, nullable=True)  # 存储对话信息的 JSON 字段
    summery = Column(Text, nullable=True)
    timeline = Column(JSON, default=list, nullable=True)  # 新增时间线列，存储JSON格式的时间线列表
    wordcloud = Column(JSON, default=list, nullable=True)  # 新增词云列，存储 List[Dict[str, int]] 格式的数据
    created_at = Column(TIMESTAMP, default=datetime.utcnow())  # 创建时间
    updated_at = Column(TIMESTAMP, default=datetime.utcnow(), onupdate=datetime.utcnow())  # 更新时间

    def __repr__(self):
        return (
            f"<Dialogue(id={self.id}, task_id={self.task_id}, original_question={self.original_question}, "
            f"subqueries={self.subqueries}, urls={self.urls}, conversations={self.conversations}, "
            f"summery={self.summery}, timeline={self.timeline}, wordcloud={self.wordcloud})>"
        )

class WebPageDetails(Base):
    __tablename__ = 'web_page_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(512), unique=True, nullable=False)  # URL，保证唯一性
    title = Column(String(255), nullable=True)  # 网页标题
    body = Column(Text, nullable=True)  # 网页正文内容
    content = Column(Text, nullable=True)  # 网页内容
    image_urls = Column(JSON, default=list)  # 存储图像 URL 列表
