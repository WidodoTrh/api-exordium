from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from sqlalchemy.orm import Session
from app.api import crud
from app import schemas
from app.config import settings
from app.deps import get_db
import jwt
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenRequest(BaseModel):
    id_token: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm="HS256")
    return token

@router.post("/google")
def google_login(payload: TokenRequest, db: Session = Depends(get_db)):
    # 1) Verify ID token with google-auth
    try:
        idinfo = id_token.verify_oauth2_token(payload.id_token, grequests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_sub = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name")
    picture = idinfo.get("picture")

    # 2) Find or create user
    user = crud.get_user_by_google_id(db, google_sub)
    if not user:
        user = crud.create_user(db, {
            "google_id": google_sub,
            "email": email,
            "name": name,
            "avatar_url": picture
        })
    else:
        user = crud.update_last_login(db, user)

    # 3) Issue app JWT
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserOut.from_orm(user)
    }
