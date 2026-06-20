# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.internal import router as internal_router
from app.api.v1.users import router as users_router

app = FastAPI(title="命理运势系统", version="1.0.0")

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
