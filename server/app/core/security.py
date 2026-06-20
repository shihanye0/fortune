# -*- coding: utf-8 -*-
"""安全模块：密码哈希和 JWT"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """创建 JWT Token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """验证 JWT Token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None
