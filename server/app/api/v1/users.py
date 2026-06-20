# -*- coding: utf-8 -*-
"""个人信息管理接口"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import verify_token
from app.models.user import User


# --- 认证中间件 ---

def get_current_user(
    db: Session = Depends(get_db),
    authorization: HTTPBearer = Depends(HTTPBearer()),
) -> User:
    """从 Bearer token 解析当前用户"""

    token = authorization.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# --- Schema ---

class UpdateProfileRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)


class UpdateBirthRequest(BaseModel):
    birth_year: int = Field(..., ge=1900, le=2100)
    birth_month: int = Field(..., ge=1, le=12)
    birth_day: int = Field(..., ge=1, le=31)
    birth_hour: int = Field(..., ge=0, le=23)

    @field_validator("birth_day")
    @classmethod
    def validate_birth_date(cls, v: int, info) -> int:
        year = info.data.get("birth_year")
        month = info.data.get("birth_month")
        if year and month:
            try:
                date(year, month, v)
            except ValueError:
                raise ValueError("出生日期无效")
        return v


# --- 路由 ---

router = APIRouter(prefix="/users", tags=["个人信息"])


def _user_to_dict(user: User) -> dict:
    """用户模型转字典（脱敏）"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "birth_year": user.birth_year,
        "birth_month": user.birth_month,
        "birth_day": user.birth_day,
        "birth_hour": user.birth_hour,
        "gender": user.gender,
        "birth_location": user.birth_location,
        "push_channel": user.push_channel,
        "push_enabled": user.push_enabled,
        "push_time": user.push_time,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """获取个人信息"""
    return {"success": True, "data": _user_to_dict(current_user)}


@router.put("/me")
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新基本信息"""
    current_user.username = req.username
    db.commit()
    db.refresh(current_user)
    return {"success": True, "data": _user_to_dict(current_user)}


@router.put("/me/birth")
def update_birth(
    req: UpdateBirthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新生辰信息"""
    current_user.birth_year = req.birth_year
    current_user.birth_month = req.birth_month
    current_user.birth_day = req.birth_day
    current_user.birth_hour = req.birth_hour
    db.commit()
    db.refresh(current_user)
    return {"success": True, "data": _user_to_dict(current_user)}
