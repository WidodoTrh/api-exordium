from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from app.models.refresh_token import UserRefreshToken
import urllib.parse
import httpx

from app.models.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.secure import get_current_user_from_cookie

from app.helper.token_service import TokenService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, name: str, pict_uri: str):
    new_user = User(email=email, name=name, pict_uri=pict_uri)
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
    try:
        code = payload.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing code")

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

        print("TOKEN JSON:", token_json)

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

        print("USERINFO:", userinfo)
        
        email = userinfo.get("email")
        name = userinfo.get("name")
        pict_uri = userinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Google userinfo failed")

        # Cek / create user
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(db, email=email, name=name, pict_uri=pict_uri)

        token_service = TokenService(db)
        access_token, refresh_token, access_exp, refresh_exp = token_service.generate_tokens(user.id)

        response = JSONResponse({
            "message": "Login successful",
            "user": {"id": user.id, "email": user.email, "name": user.name},
        })

        return token_service.set_auth_cookies(response, access_token, refresh_token, access_exp, refresh_exp)

    except Exception as e:
        import traceback
        print("CALLBACK ERROR:", str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    
@router.post("/refresh")
async def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
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
    
    token_service = TokenService(db)
    access_token, new_refresh_token, access_exp, refresh_exp = token_service.generate_tokens(user_id)

    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in": int(access_exp.total_seconds()),
    })
    return token_service.set_auth_cookies(response, access_token, new_refresh_token, access_exp, refresh_exp)
    
@router.get("/m")
async def get_me(curr_usr: User = Depends(get_current_user_from_cookie)):
    
    return {
        "id": curr_usr.id,
        "email": curr_usr.email,
        "name": curr_usr.name,
        "pict_uri": curr_usr.pict_uri
    }
    
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        from app.models.refresh_token import UserRefreshToken
        db.query(UserRefreshToken).filter(UserRefreshToken.token == refresh_token).delete()
        db.commit()

    response = JSONResponse({"message": "Logged Out"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response