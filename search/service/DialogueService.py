from typing import List, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from MySearch.database.database import DatabaseManager, Dialogue,WebPageDetails
from MySearch.database.schema import DialogueSchema, WebPageDetailsSchema
import json
class DialogueService:
    """任务服务类，封装 TaskRecord 表的操作"""

    def __init__(self):
        self.db = DatabaseManager()

    def create_dialogue(self, dialogue: DialogueSchema):
        session = self.db.get_session()
        with session as sess:
            db_dialogue = Dialogue(
                task_id=dialogue.task_id,
                original_question=dialogue.original_question,
                subqueries=dialogue.subqueries,
                urls=dialogue.urls,
                timeline=dialogue.timeline,
                summery=dialogue.summery,
                wordcloud=dialogue.wordcloud,
                conversations=dialogue.conversations
            )
            sess.add(db_dialogue)
            sess.commit()
            sess.refresh(db_dialogue)
            return db_dialogue

    def get_dialogue(self, task_id: str):
        session = self.db.get_session()
        with session as sess:
            db_dialogue = sess.query(Dialogue).filter(Dialogue.task_id == task_id).first()
            if db_dialogue:
                dialogue_schema = DialogueSchema(
                    task_id=db_dialogue.task_id,
                    original_question=db_dialogue.original_question,
                    subqueries=db_dialogue.subqueries,
                    urls=db_dialogue.urls,
                    conversations=db_dialogue.conversations
                )
                return dialogue_schema
            return None

    def update_dialogue(self, task_id: str, dialogue: DialogueSchema):
        session = self.db.get_session()
        with session as sess:
            db_dialogue = sess.query(Dialogue).filter(Dialogue.task_id == task_id).first()

            db_dialogue.original_question = dialogue.original_question
            db_dialogue.subqueries = dialogue.subqueries
            db_dialogue.urls = dialogue.urls
            db_dialogue.conversations = dialogue.conversations
            sess.commit()
            sess.refresh(db_dialogue)
            return db_dialogue

    def delete_dialogue(self, task_id: str):
        db_dialogue = self.session.query(Dialogue).filter(Dialogue.task_id == task_id).first()
        self.session.delete(db_dialogue)
        self.session.commit()
        return {"detail": "Dialogue deleted successfully"}

    def get_all_dialogues(self, page: int = 1, page_size: int = 10) -> Tuple[List[DialogueSchema], int]:
        """获取分页的 dialogues"""
        session = self.db.get_session()
        with session as sess:
            # 计算 offset
            offset = (page - 1) * page_size

            # 查询分页数据
            dialogues = sess.query(Dialogue).offset(offset).limit(page_size).all()

            # 查询总记录数
            total = sess.query(Dialogue).count()

            # 将 SQLAlchemy 对象转换为 Pydantic 模型
            dialogue_schemas = [
                DialogueSchema(
                    task_id=dialogue.task_id,
                    original_question=dialogue.original_question,
                    subqueries=dialogue.subqueries,
                    urls=dialogue.urls,
                    conversations=dialogue.conversations,
                    timeline=dialogue.timeline,
                    summery=dialogue.summery,
                    wordcloud=dialogue.wordcloud
                )
                for dialogue in dialogues
            ]

            return dialogue_schemas, total

    # WebPageDetails 模型的增删改查操作

    def create_web_page_details(self, web_page: WebPageDetailsSchema):
        image_urls_json = json.dumps(web_page.image_urls)
        sql = text("""
                INSERT IGNORE INTO web_page_details (task_id, url, title, body, content, image_urls)
                VALUES (:task_id, :url, :title, :body, :content, :image_urls)
            """)
        params = {
            'task_id': web_page.task_id,
            'url': web_page.url,
            'title': web_page.title,
            'body': web_page.body,
            'content': web_page.content,
            'image_urls': image_urls_json
        }

        # 获取数据库 session 并执行
        session = self.db.get_session()
        with session as sess:
            sess.execute(sql, params)
            sess.commit()

    def get_web_page_by_url(self, url: str):
        db_web_page = self.session.query(WebPageDetailsSchema).filter(WebPageDetailsSchema.url == url).first()
        return db_web_page

    # def update_web_page_details(url: str, web_page: WebPageDetailsSchema, db: Session):
    #     db_web_page = db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
    #     if db_web_page is None:
    #         raise HTTPException(status_code=404, detail="WebPageDetails not found")
    #     db_web_page.title = web_page.title
    #     db_web_page.body = web_page.body
    #     db_web_page.content = web_page.content
    #     db_web_page.image_urls = web_page.image_urls
    #     db.commit()
    #     db.refresh(db_web_page)
    #     return db_web_page
    #
    # def delete_web_page_details(url: str, db: Session):
    #     db_web_page = db.query(WebPageDetails).filter(WebPageDetails.url == url).first()
    #     if db_web_page is None:
    #         raise HTTPException(status_code=404, detail="WebPageDetails not found")
    #     db.delete(db_web_page)
    #     db.commit()
    #     return {"detail": "WebPageDetails deleted successfully"}
    #
    # def get_all_web_pages(db: Session):
    #     return db.query(WebPageDetails).all()


if __name__ == "__main__":
    service = DialogueService()
    dialogues = service.get_all_dialogues()
    for dialogue in dialogues:
        print(dialogue)
        print("\n")
    # dialogue_instance = DialogueSchema(
    #     task_id="123e4567-e89b-12d3-a456-426614174000",
    #     original_question="lgq",
    #     subqueries=["123","3345"]
    # )
    # # service.create_dialogue(dialogue_instance)
    # # dialogue = service.get_dialogue("123e4567-e89b-12d3-a456-426614174000")
    # # dialogue.original_question = "zhangsan"
    # # service.update_dialogue("123e4567-e89b-12d3-a456-426614174000",dialogue)
    # # print(dialogue)
    # webpagedetail = WebPageDetailsSchema(
    #     task_id="123e4567-e89b-12d3-a456-426614174000",
    #     url="www.baidu.com",
    #     title="baidu",
    #     body="baidu",
    #     image_urls=["13","q3e3"],
    #     content="erawerwer"
    # )
    # service.create_web_page_details(webpagedetail)