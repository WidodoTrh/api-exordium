from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.models.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.user import UserResponse

from app.core.secure import get_current_user_from_cookie

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/login")
def google_login(token: str, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        userid = idinfo["sub"]
        email = idinfo.get("email")
        name = idinfo.get("name")

        user = db.query(User).filter(User.google_id == userid).first()
        if not user:
            user = User(
                google_id=userid,
                email=email,
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        access_token = create_access_token(data={"sub": str(user.id)}) # tadi nya ini adalah integer karna ID. meanwhile kalo integer ga bisa di decode sama jwt. dan ternyata harus dirubah jd string
        res = JSONResponse(content = {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "google_id": user.google_id
            }
        })
        
        res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite=None,
            max_age=60*60*24*7,
            domain="exordium.id"
        )
        
        return res
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
@router.post("/logout")
def logout():
    response = Response()
    response.delete_cookie(
        key="access_token",
        domain="exordium.id",
        secure=True,
        httponly=True,
        samesite="none"
    )
    return response

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user_from_cookie)):
    return current_user

