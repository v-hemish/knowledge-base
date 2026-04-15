from fastapi import FastAPI
from api.v1.api import router
from db.db import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)


app.include_router(router)
