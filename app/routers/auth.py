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

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/auth/google")
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
        access_token = create_access_token(data={"sub": user.id})
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
    
@router.post("/auth/logout")
def logout():
    response = Response()
    response.delete_cookie("access_token")
    return response

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user_from_cookie)):
    return current_user

