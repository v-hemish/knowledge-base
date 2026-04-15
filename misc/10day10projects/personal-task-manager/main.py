from fastapi import FastAPI
from app.routes import router
import uuid

app = FastAPI()


app.include_router(router)

