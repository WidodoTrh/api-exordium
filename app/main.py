from fastapi import FastAPI
from app.models.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, user

app = FastAPI()

origins = [
    "http://localhost:5173",   # kalau develop dengan vite
    "http://exordium.id",      # domain frontend
    "https://exordium.id",     # versi https
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
app.include_router(auth.router, tags=["auth"])
