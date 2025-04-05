from pydantic import BaseModel
from typing import List, Optional

class WebPageDetailsSchema(BaseModel):
    task_id:str
    url: str
    title: Optional[str]
    body: Optional[str]
    content: Optional[str]
    image_urls: List[str] = []

class DialogueSchema(BaseModel):
    task_id: str
    original_question: str
    subqueries: List[str] = []
    urls: List[str] = []
    conversations: List[dict] = []
    timeline: List[dict] = []
    summery: str
