from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from app.models.user_privacy import UserPrivacy

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserPrivacyController:
    @staticmethod
    def set_or_update_password(db: Session, user_id: int, password: str):
        if not password or len(password) < 8:
            return JSONResponse(
                content={"message": "Password must be at least 8 characters"},
                status_code=422
            )

        hashed = pwd_context.hash(password)
        privacy = db.query(UserPrivacy).filter(UserPrivacy.user_id == user_id).first()

        if privacy:
            privacy.user_password = hashed
        else:
            privacy = UserPrivacy(user_id=user_id, user_password=hashed)
            db.add(privacy)

        db.commit()
        return JSONResponse(content={"message": "Password has been set successfully"}, status_code=200)
