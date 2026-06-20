# -*- coding: utf-8 -*-
"""认证接口"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已注册
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "EMAIL_EXISTS", "message": "该邮箱已被注册"},
            },
        )

    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        birth_year=req.birth_year,
        birth_month=req.birth_month,
        birth_day=req.birth_day,
        birth_hour=req.birth_hour,
        gender=req.gender,
        birth_location=req.birth_location,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成 Token
    token = create_access_token(user_id=user.id)

    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "token": token,
        },
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.email == req.email).first()

    # 验证用户存在且密码正确（不暴露邮箱是否存在）
    if not user or not verify_password(req.password, user.password_hash):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {"code": "LOGIN_FAILED", "message": "邮箱或密码错误"},
            },
        )

    # 生成 Token
    token = create_access_token(user_id=user.id)

    return {
        "success": True,
        "data": {
            "token": token,
        },
    }
