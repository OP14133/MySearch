from fastapi import APIRouter
from ..models.query import Query
# from services.search_service import handle_query

router = APIRouter()

@router.post("/retrieve/")
async def retrieve(query: Query):
    # response = await handle_query(query)
    response = "hello,world"
    return response
