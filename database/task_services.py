from db import SessionLocal
from models import Dialogue, WebPageDetails
from schema import DialogueSchema, WebPageDetailsSchema
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException

# 数据库会话管理
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dialogue 模型的增删改查操作

def create_dialogue(dialogue: DialogueSchema, db: Session):
    db_dialogue = Dialogue(
        task_id=dialogue.task_id,
        original_question=dialogue.original_question,
        subqueries=dialogue.subqueries,
        urls=dialogue.urls,
        conversations=dialogue.conversations
    )
    db.add(db_dialogue)
    db.commit()
    db.refresh(db_dialogue)
    return db_dialogue

def get_dialogue(task_id: str, db: Session):
    db_dialogue = db.query(Dialogue).filter(Dialogue.task_id == task_id).first()
    if db_dialogue is None:
        raise HTTPException(status_code=404, detail="Dialogue not found")
    return db_dialogue

def update_dialogue(task_id: str, dialogue: DialogueSchema, db: Session):
    db_dialogue = db.query(Dialogue).filter(Dialogue.task_id == task_id).first()
    if db_dialogue is None:
        raise HTTPException(status_code=404, detail="Dialogue not found")
    db_dialogue.original_question = dialogue.original_question
    db_dialogue.subqueries = dialogue.subqueries
    db_dialogue.urls = dialogue.urls
    db_dialogue.conversations = dialogue.conversations
    db.commit()
    db.refresh(db_dialogue)
    return db_dialogue

def delete_dialogue(task_id: str, db: Session):
    db_dialogue = db.query(Dialogue).filter(Dialogue.task_id == task_id).first()
    if db_dialogue is None:
        raise HTTPException(status_code=404, detail="Dialogue not found")
    db.delete(db_dialogue)
    db.commit()
    return {"detail": "Dialogue deleted successfully"}

def get_all_dialogues(db: Session):
    return db.query(Dialogue).all()

# WebPageDetails 模型的增删改查操作

def create_web_page_details(web_page: WebPageDetailsSchema, db: Session):
    db_web_page = WebPageDetails(
        task_id=web_page.task_id,
        url=web_page.url,
        title=web_page.title,
        body=web_page.body,
        content=web_page.content,
        image_urls=web_page.image_urls
    )
    db.add(db_web_page)
    db.commit()
    db.refresh(db_web_page)
    return db_web_page

def get_web_page_by_url(url: str, db: Session):
    db_web_page = db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
    if db_web_page is None:
        raise HTTPException(status_code=404, detail="WebPageDetails not found")
    return db_web_page

def update_web_page_details(url: str, web_page: WebPageDetailsSchema, db: Session):
    db_web_page = db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
    if db_web_page is None:
        raise HTTPException(status_code=404, detail="WebPageDetails not found")
    db_web_page.title = web_page.title
    db_web_page.body = web_page.body
    db_web_page.content = web_page.content
    db_web_page.image_urls = web_page.image_urls
    db.commit()
    db.refresh(db_web_page)
    return db_web_page

def delete_web_page_details(url: str, db: Session):
    db_web_page = db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
    if db_web_page is None:
        raise HTTPException(status_code=404, detail="WebPageDetails not found")
    db.delete(db_web_page)
    db.commit()
    return {"detail": "WebPageDetails deleted successfully"}

def get_all_web_pages(db: Session):
    return db.query(WebPageDetails).all()