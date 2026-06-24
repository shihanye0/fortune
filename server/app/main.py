# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.divination import router as divination_router
from app.api.v1.fortunes import router as fortunes_router
from app.api.v1.internal import router as internal_router
from app.api.v1.prediction_outcomes import router as prediction_outcomes_router
from app.api.v1.probability_events import router as probability_events_router
from app.api.v1.users import router as users_router

app = FastAPI(title="命理运势系统", version="1.0.0")

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(divination_router, prefix="/api/v1")
app.include_router(fortunes_router, prefix="/api/v1")
app.include_router(prediction_outcomes_router, prefix="/api/v1")
app.include_router(probability_events_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
