# -*- coding: utf-8 -*-
"""占卜接口"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.users import get_current_user
from app.models.divination_record import DivinationRecord
from app.models.user import User


router = APIRouter(prefix="/divination", tags=["占卜功能"])


# --- Schema ---

class LiuyaoRequest(BaseModel):
    question: str | None = None
    method: str = Field(default="coin", pattern=r"^(coin|time)$")


class QimenRequest(BaseModel):
    question: str | None = None
    mode: str = Field(..., pattern=r"^(question|realtime)$")


# --- 路由 ---

@router.post("/liuyao")
def do_liuyao(
    req: LiuyaoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """六爻占卜"""
    from fortune_engine.liuyao.hexagram import coin_divination
    from fortune_engine.services.deepseek import interpret_liuyao

    # 起卦
    question = req.question or ""
    hexagram_data = coin_divination(question)

    # LLM 解读
    interpretation = interpret_liuyao(hexagram_data)

    # 存储记录
    record = DivinationRecord(
        user_id=current_user.id,
        type="liuyao",
        question=question or None,
        raw_data=hexagram_data,
        llm_interpretation=interpretation,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "data": {
            "id": record.id,
            "question": question or None,
            "hexagram": hexagram_data,
            "interpretation": interpretation,
        },
    }


@router.post("/qimen")
def do_qimen(
    req: QimenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """奇门遁甲排盘"""
    from datetime import datetime
    from fortune_engine.qimen.chart import calculate_qimen
    from fortune_engine.services.deepseek import interpret_qimen

    # 获取当前时间
    now = datetime.now()
    question = req.question or ""

    # 排盘
    chart_data = calculate_qimen(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
    )

    # LLM 解读
    interpretation = interpret_qimen(chart_data, question)

    # 存储记录
    record = DivinationRecord(
        user_id=current_user.id,
        type="qimen",
        question=question or None,
        raw_data=chart_data,
        llm_interpretation=interpretation,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "data": {
            "id": record.id,
            "question": question or None,
            "chart": chart_data,
            "interpretation": interpretation,
        },
    }
