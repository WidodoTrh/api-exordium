from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
import requests
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
def login():
    google_auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = "openid email profile"
    response_type = "code"

    url = (
        f"{google_auth_endpoint}"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type={response_type}"
        f"&scope={scope}"
    )

    return RedirectResponse(url)

@router.get("/callback")
def callback(code: str):
    token_endpoint = "https://oauth2.googleapis.com/token"

    # Exchange code jadi access token
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    token_res = requests.post(token_endpoint, data=payload)
    token_json = token_res.json()

    if "error" in token_json:
        raise HTTPException(status_code=400, detail=token_json)

    access_token = token_json["access_token"]
    id_token = token_json["id_token"]

    userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    userinfo_res = requests.get(
        userinfo_endpoint, headers={"Authorization": f"Bearer {access_token}"}
    )
    userinfo = userinfo_res.json()
    return {"access_token": access_token, "id_token": id_token, "userinfo": userinfo}
