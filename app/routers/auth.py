from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session
import urllib.parse

from app.models.database import get_db
from app.config import settings
from app.models.user import User
from app.core.secure import get_current_user_from_cookie

from app.helper.token_service import TokenService
from app.schemas.set_pass import SetPasswordRequest
from app.controllers.user_privacy_controller import UserPrivacyController
from app.controllers.auth_controller import AuthController


router = APIRouter()

@router.post("/signin")
async def login(payload: dict, response: Response, db: Session = Depends(get_db)):
    con = AuthController(db)
    return await con.login(payload, response)

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
    controller = AuthController(db)
    return await controller.google_login_callback(payload)

@router.post("/refresh")
async def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    controller = AuthController(db)
    return await controller.refresh_access_token(request, response)
    
@router.get("/m")
async def get_me(curr_usr: User = Depends(get_current_user_from_cookie)):    
    return JSONResponse(
        status_code=200,
        content={
            "id": curr_usr.id,
            "email": curr_usr.email,
            "name": curr_usr.name,
            "pict_uri": curr_usr.pict_uri
        }
    )
    
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    controller = AuthController(db)
    return await controller.logout(request)

@router.post("/set-pass")
async def set_password(body: SetPasswordRequest, db: Session = Depends(get_db), curr_usr: User = Depends(get_current_user_from_cookie)):
    return UserPrivacyController.set_or_update_password(db, curr_usr.id, body.p)