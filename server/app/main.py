# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="命理运势系统", version="1.0.0")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
