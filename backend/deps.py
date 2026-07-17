from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException

from db import SessionLocal, User
from security import decode_access_token


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def get_current_user(authorization: Optional[str] = Header(None), db=Depends(get_db)) -> User:
    token = _extract_token(authorization)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(401, "Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return user


def get_optional_user(authorization: Optional[str] = Header(None), db=Depends(get_db)) -> Optional[User]:
    token = _extract_token(authorization)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()
