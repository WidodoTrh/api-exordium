from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
import urllib.parse
import httpx

from app.models.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.user import UserResponse

from app.core.secure import get_current_user_from_cookie
from app.helper.auth_helpers import store_refresh_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=30))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, name: str):
    new_user = User(email=email, name=name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/google/login")
def login_with_google():
    google_auth_endpoint = settings.GOOGLE_OAUTH_ENDPOINT
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.APP_REDIRECT_URI, 
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = google_auth_endpoint + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)

@router.post("/google/callback")
async def google_callback(payload: dict, db: Session = Depends(get_db)):
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # --- Tukar code ke Google ---
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.APP_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(settings.GOOGLE_TOKEN_ENDPOINT, data=data)
        token_json = token_res.json()

    if "error" in token_json:
        raise HTTPException(status_code=400, detail=token_json["error"])

    # Ambil data user dari google
    access_token = token_json["access_token"]
    async with httpx.AsyncClient() as client:
        userinfo_res = await client.get(
            settings.GOOGLE_OAUTH_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo = userinfo_res.json()

    email = userinfo.get("email")
    name = userinfo.get("name")
    if not email:
        raise HTTPException(status_code=400, detail="Google userinfo failed")

    # Cek 
    user = get_user_by_email(db, email)
    if not user:
        user = create_user(db, email=email, name=name)

    # Buat token lokal
    access_token_expires = timedelta(minutes=1)
    refresh_token_expires = timedelta(days=30)

    jwt_access_token = create_access_token({"sub": str(user.id)}, expires_delta=access_token_expires)
    jwt_refresh_token = create_refresh_token({"sub": str(user.id)}, expires_delta=refresh_token_expires)

    store_refresh_token(
        db=db,
        user_id=user.id,
        token=jwt_refresh_token,
        expires_at=datetime.utcnow() + refresh_token_expires,
    )

    # --- Set cookies ---
    response = JSONResponse({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    })
    response.set_cookie(
        key="access_token",
        value=jwt_access_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=int(access_token_expires.total_seconds())
    )
    response.set_cookie(
        key="refresh_token",
        value=jwt_refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=int(refresh_token_expires.total_seconds())
    )
    return response
    
@router.post("/refresh")
async def refresh_access_token(payload: dict, db: Session = Depends(get_db)):
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh token")

    # Verifikasi JWT refresh token
    try:
        decoded_token = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if decoded_token.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = decoded_token.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from app.models.refresh_token import UserRefreshToken
    db_token = (
        db.query(UserRefreshToken)
        .filter(
            UserRefreshToken.user_id == user_id,
            UserRefreshToken.token == refresh_token,
        )
        .first()
    )

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Generate token baru
    access_token_expires = timedelta(hours=1)
    refresh_token_expires = timedelta(days=30)

    new_access_token = create_access_token({"sub": str(user_id)}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token({"sub": str(user_id)}, expires_delta=refresh_token_expires)
    
    store_refresh_token(
        db=db,
        user_id=user_id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + refresh_token_expires,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }
    
@router.get("/m")
async def get_me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing"
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }
    
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        from app.models.refresh_token import UserRefreshToken
        db.query(UserRefreshToken).filter(UserRefreshToken.token == refresh_token).delete()
        db.commit()

    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response