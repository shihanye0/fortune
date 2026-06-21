# -*- coding: utf-8 -*-
"""个人信息管理接口"""
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import verify_password, verify_token
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


class PushSettingsRequest(BaseModel):
    push_enabled: bool
    push_channel: str = Field(..., pattern=r"^(email|feishu|both)$")
    push_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    feishu_webhook: str | None = None

    @field_validator("push_time")
    @classmethod
    def validate_push_time(cls, v: str) -> str:
        hh, mm = v.split(":")
        if int(hh) > 23 or int(mm) > 59:
            raise ValueError("时间格式无效")
        return v


class LLMSettingsRequest(BaseModel):
    """LLM配置请求"""
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_api_url: str | None = None
    llm_model: str | None = None


class DeleteAccountRequest(BaseModel):
    password: str


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
        "feishu_webhook": user.feishu_webhook,
        "llm_provider": user.llm_provider,
        "llm_api_key": user.llm_api_key[:8] + "***" if user.llm_api_key else None,
        "llm_api_url": user.llm_api_url,
        "llm_model": user.llm_model,
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


@router.put("/me/push-settings")
def update_push_settings(
    req: PushSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新推送设置"""
    # 飞书/both 渠道必须提供 webhook
    if req.push_channel in ("feishu", "both") and req.push_enabled:
        if not req.feishu_webhook or not req.feishu_webhook.strip():
            raise HTTPException(status_code=400, detail="飞书推送需要填写 Webhook URL")

    current_user.push_enabled = req.push_enabled
    current_user.push_channel = req.push_channel
    current_user.push_time = req.push_time
    current_user.feishu_webhook = req.feishu_webhook
    db.commit()
    db.refresh(current_user)
    return {"success": True, "data": _user_to_dict(current_user)}


@router.put("/me/llm-settings")
def update_llm_settings(
    req: LLMSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新LLM配置"""
    current_user.llm_provider = req.llm_provider
    current_user.llm_api_key = req.llm_api_key
    current_user.llm_api_url = req.llm_api_url
    current_user.llm_model = req.llm_model
    db.commit()
    db.refresh(current_user)
    return {"success": True, "data": _user_to_dict(current_user)}


@router.delete("/me")
def delete_account(
    req: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """注销账号"""
    if not verify_password(req.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="密码错误，无法注销")

    db.delete(current_user)
    db.commit()
    return {"success": True, "message": "账号已注销"}
