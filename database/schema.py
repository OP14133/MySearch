from pydantic import BaseModel
from typing import List, Optional

class WebPageDetailsSchema(BaseModel):
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
    conversations: Optional[dict] = None

    class Config:
        orm_mode = True
