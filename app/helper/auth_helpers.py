from datetime import datetime
from app.models.refresh_token import UserRefreshToken

def store_refresh_token(db, user_id: int, token: str, expires_at: datetime):
    db.query(UserRefreshToken).filter(UserRefreshToken.user_id == user_id).delete()

    new_token = UserRefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token
