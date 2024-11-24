from typing import List

from pydantic import BaseModel, Field
"""
定义了结构化的数据模型，用于表示子主题（Subtopic）及其集合（Subtopics）。通过使用 Pydantic，代码提供了数据验证功能，确保在创建这些模型时传入的数据符合预期的格式和规则。这种设计通常用于处理API请求和响应的数据结构。
"""
class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)

class Subtopics(BaseModel):
    subtopics: List[Subtopic] = []
