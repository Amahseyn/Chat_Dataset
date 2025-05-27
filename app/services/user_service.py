# app/services/user_service.py
from sqlalchemy.orm import Session
from models.user_model import User
from core.security import get_password_hash
from schemas.user_schema import UserCreate
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    if get_user_by_username(db, user.username):
        raise ValueError("Username already taken")
    if get_user_by_email(db, user.email):
        raise ValueError("Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user