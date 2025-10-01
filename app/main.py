from fastapi import FastAPI
from app.models.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, user, data

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://exordium.id",
    "https://exordium.id",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(user.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(data.router, prefix="/data", tags=["data"])
