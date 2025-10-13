from sqlalchemy.orm import Session
from app.models import models
from app.models.user import User
from datetime import datetime


def get_user_by_google_id(db: Session, google_id: str):
    return db.query(models.User).filter(models.User.google_id == google_id).first()

def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, name: str, pict_uri: str):
    new_user = User(email=email, name=name, pict_uri=pict_uri)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_last_login(db: Session, user: models.User):
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



