from fastapi import FastAPI
from app.database import engine
from app.models.mybaseclasses import Base
from app.routes import users

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(users.router) 