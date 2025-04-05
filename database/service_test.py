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
dialogue_data = DialogueSchema(
        task_id=str(uuid.uuid4()),
        original_question="What is the meaning of life?",
        subqueries=["life", "universe", "everything"],
        urls=["http://example.com"],
        conversations={"user": "What is the meaning of life?", "bot": "42"}
    )
# Base.metadata.create_all(engine)
session = SessionLocal()
create_dialogue(dialogue_data, session)