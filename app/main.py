from fastapi import FastAPI
from app.models.database import init_db
from app.routers import user

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(user.router)
