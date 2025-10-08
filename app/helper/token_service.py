from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from jose import jwt
from app.config import settings
from app.models.refresh_token import UserRefreshToken
from app.core.secure import create_access_token, create_refresh_token

class TokenService:
    def __init__(self, db):
        self.db = db

    def generate_tokens(self, user_id: int):
        access_token_expires = timedelta(minutes=1)
        refresh_token_expires = timedelta(days=30)

        access_token = create_access_token({"sub": str(user_id)}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token({"sub": str(user_id)}, expires_delta=refresh_token_expires)

        db_token = UserRefreshToken(
            user_id=user_id,
            token=refresh_token,
            expires_at=datetime.utcnow() + refresh_token_expires,
        )
        self.db.add(db_token)
        self.db.commit()

        return access_token, refresh_token, access_token_expires, refresh_token_expires

    def set_auth_cookies(self, response: JSONResponse, access_token: str, refresh_token: str, access_exp: timedelta, refresh_exp: timedelta):
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=int(access_exp.total_seconds()),
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=int(refresh_exp.total_seconds()),
        )
        return response
