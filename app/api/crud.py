from sqlalchemy.orm import Session
from app.models import models
from datetime import datetime

def get_user_by_google_id(db: Session, google_id: str):
    return db.query(models.User).filter(models.User.google_id == google_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: dict):
    user = models.User(
        google_id=user_in["google_id"],
        email=user_in["email"],
        name=user_in.get("name"),
        avatar_url=user_in.get("avatar_url")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_last_login(db: Session, user: models.User):
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
