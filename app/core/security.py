# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from app.core.deps import get_db
from sqlalchemy.orm import Session
from sqlalchemy_utils import StringEncryptedType

from app.core.config import settings


key = settings.DB_SECRET_KEY

SECRET_KEY = settings.JWT_SECRET_KEY

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    encrypted_plain_password = StringEncryptedType(key=key).process_bind_param(plain_password, dialect=None)

    return encrypted_plain_password == hashed_password

def get_password_hash(password: str) -> str:
    encrypted_type = StringEncryptedType(key=key).process_bind_param(password, dialect=None)
    return encrypted_type

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    
    to_encode = data.copy()    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)    
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return payload
    except JWTError:
        return None
