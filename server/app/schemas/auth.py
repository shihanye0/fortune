# -*- coding: utf-8 -*-
"""认证相关 Schema"""
import re
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    birth_year: int = Field(..., ge=1900, le=2100)
    birth_month: int = Field(..., ge=1, le=12)
    birth_day: int = Field(..., ge=1, le=31)
    birth_hour: int = Field(..., ge=0, le=23)
    gender: int = Field(..., ge=0, le=1)
    birth_location: str | None = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含字母和数字")
        return v

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
            if date(year, month, v) > date.today():
                raise ValueError("出生日期不能是未来日期")
        return v


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    """注册响应"""
    id: int
    username: str
    email: str
    token: str


class ApiResponse(BaseModel):
    """统一响应格式"""
    success: bool
    data: RegisterResponse | None = None
    error: dict | None = None
