from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from jose import jwt
import uuid
import secrets
from app.config import settings
from app.models.refresh_token import UserRefreshToken
from app.core.secure import create_access_token, create_refresh_token

class TokenService:
    def __init__(self, db):
        self.db = db

    def generate_tokens(self, user_id: int):
        session_id = str(uuid.uuid4())
        
        access_token_expires = timedelta(days=1)
        refresh_token_expires = timedelta(days=30)
        
        self.db.query(UserRefreshToken).filter(UserRefreshToken.user_id == user_id).delete()
        self.db.commit()

        access_token, access_jti = create_access_token({"sub": str(user_id), "session_id": session_id}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token({"sub": str(user_id), "session_id": session_id}, expires_delta=refresh_token_expires)

        db_token = UserRefreshToken(
            user_id=user_id,
            token=refresh_token,
            session_id=session_id,
            expires_at=datetime.utcnow() + refresh_token_expires,
            created_at=datetime.utcnow().replace(microsecond=0)
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
        
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="XSRF-TOKEN",
            value=csrf_token,
            httponly=False,
            secure=True,
            samesite="None",
            domain=settings.APP_ROOT_DOMAIN,
            max_age=int(access_exp.total_seconds()),
        )
        
        return response
