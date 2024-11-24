from fastapi import FastAPI
from routers import retrieval

app = FastAPI()

app.include_router(retrieval.router)
