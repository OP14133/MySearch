from sqlalchemy.orm import Session
from .models import Dialogue, WebPageDetails
from .schemas import DialogueSchema, WebPageDetailsSchema

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    # Create a new Dialogue
    def create_dialogue(self, dialogue_data: DialogueSchema):
        dialogue = Dialogue(**dialogue_data.dict())
        self.db.add(dialogue)
        self.db.commit()
        self.db.refresh(dialogue)
        return dialogue

    # Get a Dialogue by task_id
    def get_dialogue_by_task_id(self, task_id: str):
        return self.db.query(Dialogue).filter(Dialogue.task_id == task_id).first()

    # Update an existing Dialogue
    def update_dialogue(self, task_id: str, updated_data: DialogueSchema):
        dialogue = self.db.query(Dialogue).filter(Dialogue.task_id == task_id).first()
        if dialogue:
            for key, value in updated_data.dict().items():
                setattr(dialogue, key, value)
            self.db.commit()
            self.db.refresh(dialogue)
        return dialogue

    # Delete a Dialogue by task_id
    def delete_dialogue(self, task_id: str):
        dialogue = self.db.query(Dialogue).filter(Dialogue.task_id == task_id).first()
        if dialogue:
            self.db.delete(dialogue)
            self.db.commit()
        return dialogue

    # Create a new WebPageDetails entry
    def create_web_page_details(self, webpage_data: WebPageDetailsSchema, dialogue_id: int):
        webpage = WebPageDetails(**webpage_data.dict(), dialogue_id=dialogue_id)
        self.db.add(webpage)
        self.db.commit()
        self.db.refresh(webpage)
        return webpage

    # Get WebPageDetails by URL
    def get_web_page_by_url(self, url: str):
        return self.db.query(WebPageDetails).filter(WebPageDetails.url == url).first()

    # Delete a WebPageDetails by URL
    def delete_web_page_by_url(self, url: str):
        webpage = self.db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
        if webpage:
            self.db.delete(webpage)
            self.db.commit()
        return webpage
