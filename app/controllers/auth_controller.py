import httpx
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext

from app.config import settings
from app.models.refresh_token import UserRefreshToken
from app.helper.token_service import TokenService
from app.models.user import User
from app.api.crud import create_user, get_user_by_email
from app.core.crypto import decrypt_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# token_service = TokenService()

class AuthController:
    def __init__(self, db):
        self.db = db
       
    # login biasa pake email & password =============================================================================
    async def login(self, payload: dict, response: JSONResponse):
        db = self.db
        token_service = TokenService(db)

        email = payload.get("_e")
        encrypted_password = payload.get("_p")

        if not email or not encrypted_password:
            raise HTTPException(status_code=400, detail="Email and password required")

        user = (
            db.query(User)
            .options(joinedload(User.privacy))
            .filter(User.email == email)
            .first()
        )

        if not user or not user.privacy:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        try:
            password = decrypt_password(encrypted_password)
        except Exception as e:
            print("decrypt error:", e)
            raise HTTPException(status_code=400, detail="Invalid encryption data")

        if not pwd_context.verify(password, user.privacy.user_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token, refresh_token, access_exp, refresh_exp = token_service.generate_tokens(user.id)
        response = JSONResponse(content={"message": "Login succeed", "user": user.email})
        return token_service.set_auth_cookies(response, access_token, refresh_token, access_exp, refresh_exp)

    # refresh & access token ==========================================================================================
    async def refresh_access_token(self, request: Request, response: Response):
        db = self.db
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

        res = JSONResponse({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": int(access_exp.total_seconds()),
        })
        return token_service.set_auth_cookies(res, access_token, new_refresh_token, access_exp, refresh_exp)
    
    # calback code ==========================================================================================
    async def google_login_callback(self, payload: dict):
        db = self.db
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

            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                    token_res = await client.post(settings.GOOGLE_TOKEN_ENDPOINT, data=data)
                    token_json = token_res.json()
            except httpx.ConnectTimeout:
                raise HTTPException(status_code=500, detail="Connection to Google timed out")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=str(e))

            if "error" in token_json:
                raise HTTPException(status_code=400, detail=token_json["error"])

            # Ambil data user dari google
            access_token = token_json.get("access_token")
            async with httpx.AsyncClient() as client:
                userinfo_res = await client.get(
                    settings.GOOGLE_OAUTH_USERINFO,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                userinfo = userinfo_res.json()

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
        
    async def logout(self, request: Request):
        refresh_token = request.cookies.get("refresh_token")

        if refresh_token:
            self.db.query(UserRefreshToken).filter(
                UserRefreshToken.token == refresh_token
            ).delete()
            self.db.commit()

        response = JSONResponse({"message": "Logged Out"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response