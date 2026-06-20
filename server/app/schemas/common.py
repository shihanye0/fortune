# -*- coding: utf-8 -*-
"""通用 Schema"""
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一响应格式"""
    success: bool
    data: dict | None = None
    error: dict | None = None
