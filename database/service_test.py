from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, SessionLocal, engine
from models import Dialogue, WebPageDetails
from schema import DialogueSchema, WebPageDetailsSchema
from task_services import (
    create_dialogue, get_dialogue, update_dialogue, delete_dialogue, get_all_dialogues,
    create_web_page_details, get_web_page_by_url, update_web_page_details, delete_web_page_details, get_all_web_pages
)
import uuid
from fastapi import HTTPException

# 使用 SQLite 内存数据库进行测试

def tables(engine):
    """创建和删除数据库表"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

def session(engine):
    """返回一个数据库会话"""
    SessionLocal.configure(bind=engine)  # 使用传入的引擎
    db_session = SessionLocal()
    yield db_session
    db_session.rollback()  # 回滚事务
    db_session.close()  # 关闭会话

# 测试创建 Dialogue 记录
def test_create_dialogue(session):
    dialogue_data = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="What is the meaning of life?",
        subqueries=["life", "universe", "everything"],
        urls=["http://example.com"],
        conversations={"user": "What is the meaning of life?", "bot": "42"}
    )
    created_dialogue = create_dialogue(dialogue_data, session)
    db_dialogue = session.query(Dialogue).filter(Dialogue.task_id == dialogue_data.task_id).first()
    assert db_dialogue is not None
    assert db_dialogue.task_id == dialogue_data.task_id
    assert db_dialogue.original_question == dialogue_data.original_question
    assert db_dialogue.subqueries == dialogue_data.subqueries
    assert db_dialogue.urls == dialogue_data.urls
    assert db_dialogue.conversations == dialogue_data.conversations

# 测试获取 Dialogue 记录
def test_get_dialogue(session):
    dialogue_data = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="What is the meaning of life?",
        subqueries=["life", "universe", "everything"],
        urls=["http://example.com"],
        conversations={"user": "What is the meaning of life?", "bot": "42"}
    )
    create_dialogue(dialogue_data, session)
    retrieved_dialogue = get_dialogue(dialogue_data.task_id, session)
    assert retrieved_dialogue.task_id == dialogue_data.task_id
    assert retrieved_dialogue.original_question == dialogue_data.original_question

# 测试更新 Dialogue 记录
def test_update_dialogue(session):
    dialogue_data = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="What is the meaning of life?",
        subqueries=["life", "universe", "everything"],
        urls=["http://example.com"],
        conversations={"user": "What is the meaning of life?", "bot": "42"}
    )
    create_dialogue(dialogue_data, session)
    updated_data = DialogueSchema(
        task_id=dialogue_data.task_id,
        original_question="What is the purpose of life?",
        subqueries=["life", "universe", "everything", "purpose"],
        urls=["http://example.com", "http://example.org"],
        conversations={"user": "What is the purpose of life?", "bot": "42"}
    )
    updated_dialogue = update_dialogue(updated_data.task_id, updated_data, session)
    db_dialogue = session.query(Dialogue).filter(Dialogue.task_id == updated_data.task_id).first()
    assert db_dialogue.original_question == updated_data.original_question
    assert db_dialogue.subqueries == updated_data.subqueries
    assert db_dialogue.urls == updated_data.urls
    assert db_dialogue.conversations == updated_data.conversations

# 测试删除 Dialogue 记录
def test_delete_dialogue(session):
    dialogue_data = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="What is the meaning of life?",
        subqueries=["life", "universe", "everything"],
        urls=["http://example.com"],
        conversations={"user": "What is the meaning of life?", "bot": "42"}
    )
    create_dialogue(dialogue_data, session)
    delete_response = delete_dialogue(dialogue_data.task_id, session)
    assert delete_response == {"detail": "Dialogue deleted successfully"}
    db_dialogue = session.query(Dialogue).filter(Dialogue.task_id == dialogue_data.task_id).first()
    assert db_dialogue is None

# 测试获取所有 Dialogue 记录
def test_get_all_dialogues(session):
    dialogue1 = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="Question 1",
        subqueries=[],
        urls=[],
        conversations=None
    )
    create_dialogue(dialogue1, session)
    dialogue2 = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="Question 2",
        subqueries=[],
        urls=[],
        conversations=None
    )
    create_dialogue(dialogue2, session)
    all_dialogues = get_all_dialogues(session)
    assert len(all_dialogues) >= 2
    task_ids = [d.task_id for d in all_dialogues]
    assert dialogue1.task_id in task_ids
    assert dialogue2.task_id in task_ids

# 测试创建 WebPageDetails 记录
def test_create_web_page_details(session):
    web_page_data = WebPageDetailsSchema(
        url="http://example.com",
        title="Example Page",
        body="This is the body.",
        content="Full content here.",
        image_urls=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
    )
    created_web_page = create_web_page_details(web_page_data, session)
    db_web_page = session.query(WebPageDetails).filter(WebPageDetails.url == web_page_data.url).first()
    assert db_web_page is not None
    assert db_web_page.url == web_page_data.url
    assert db_web_page.title == web_page_data.title
    assert db_web_page.body == web_page_data.body
    assert db_web_page.content == web_page_data.content
    assert db_web_page.image_urls == web_page_data.image_urls

# 测试获取 WebPageDetails 记录
def test_get_web_page_by_url(session):
    web_page_data = WebPageDetailsSchema(
        url="http://example.com",
        title="Example Page",
        body="This is the body.",
        content="Full content here.",
        image_urls=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
    )
    create_web_page_details(web_page_data, session)
    retrieved_web_page = get_web_page_by_url(web_page_data.url, session)
    assert retrieved_web_page.url == web_page_data.url
    assert retrieved_web_page.title == web_page_data.title

# 测试更新 WebPageDetails 记录
def test_update_web_page_details(session):
    web_page_data = WebPageDetailsSchema(
        url="http://example.com",
        title="Example Page",
        body="This is the body.",
        content="Full content here.",
        image_urls=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
    )
    create_web_page_details(web_page_data, session)
    updated_data = WebPageDetailsSchema(
        url=web_page_data.url,
        title="Updated Title",
        body="Updated body content.",
        content="Updated full content.",
        image_urls=["http://example.com/image3.jpg", "http://example.com/image4.jpg"]
    )
    updated_web_page = update_web_page_details(updated_data.url, updated_data, session)
    db_web_page = session.query(WebPageDetails).filter(WebPageDetails.url == updated_data.url).first()
    assert db_web_page.title == updated_data.title
    assert db_web_page.body == updated_data.body
    assert db_web_page.content == updated_data.content
    assert db_web_page.image_urls == updated_data.image_urls

# 测试删除 WebPageDetails 记录
def test_delete_web_page_details(session):
    web_page_data = WebPageDetailsSchema(
        url="http://example.com",
        title="Example Page",
        body="This is the body.",
        content="Full content here.",
        image_urls=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
    )
    create_web_page_details(web_page_data, session)
    delete_response = delete_web_page_details(web_page_data.url, session)
    assert delete_response == {"detail": "WebPageDetails deleted successfully"}
    db_web_page = session.query(WebPageDetails).filter(WebPageDetails.url == web_page_data.url).first()
    assert db_web_page is None

# 测试获取不存在的 Dialogue 记录
def test_get_dialogue_not_found(session):
    with pytest.raises(HTTPException) as exc_info:
        get_dialogue("nonexistent_task_id", session)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Dialogue not found"

# 测试删除不存在的 Dialogue 记录
SessionLocal.configure(bind=engine)  # 使用传入的引擎
db_session = SessionLocal()
test_create_dialogue(db_session)