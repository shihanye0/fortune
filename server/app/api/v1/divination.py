# -*- coding: utf-8 -*-
"""占卜接口"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
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


class DivinationFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback_text: str | None = None


# --- 路由 ---

@router.post("/liuyao")
def do_liuyao(
    req: LiuyaoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """六爻占卜"""
    from fortune_engine.liuyao.hexagram import coin_divination
    from fortune_engine.bazi.pillar import calculate_bazi
    from fortune_engine.services.deepseek import interpret_liuyao

    # 起卦
    question = req.question or ""
    hexagram_data = coin_divination(question)

    # 获取用户八字信息
    bazi_info = ""
    try:
        bazi_result = calculate_bazi(
            current_user.birth_year, current_user.birth_month,
            current_user.birth_day, current_user.birth_hour,
            current_user.gender
        )
        bazi_info = (
            f"八字：{bazi_result['year_pillar']} {bazi_result['month_pillar']} "
            f"{bazi_result['day_pillar']} {bazi_result['hour_pillar']}，"
            f"日主：{bazi_result['day_master']}，"
            f"喜用神：{'、'.join(bazi_result.get('favorable_elements', []))}"
        )
    except Exception:
        pass

    # LLM 解读（结合八字）
    interpretation = interpret_liuyao(hexagram_data, bazi_info)

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
    from fortune_engine.bazi.pillar import calculate_bazi
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

    # 获取用户八字信息
    bazi_info = ""
    try:
        bazi_result = calculate_bazi(
            current_user.birth_year, current_user.birth_month,
            current_user.birth_day, current_user.birth_hour,
            current_user.gender
        )
        bazi_info = (
            f"八字：{bazi_result['year_pillar']} {bazi_result['month_pillar']} "
            f"{bazi_result['day_pillar']} {bazi_result['hour_pillar']}，"
            f"日主：{bazi_result['day_master']}，"
            f"喜用神：{'、'.join(bazi_result.get('favorable_elements', []))}"
        )
    except Exception:
        pass

    # LLM 解读（结合八字）
    interpretation = interpret_qimen(chart_data, question, bazi_info)

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


@router.get("/records")
def list_divination_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: str | None = Query(None, pattern=r"^(liuyao|qimen)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """占卜历史列表"""
    offset = (page - 1) * limit

    query = db.query(DivinationRecord).filter(
        DivinationRecord.user_id == current_user.id
    )
    if type:
        query = query.filter(DivinationRecord.type == type)

    total = query.count()

    records = (
        query.order_by(DivinationRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "success": True,
        "data": [_record_to_list_dict(r) for r in records],
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    }


@router.post("/{record_id}/feedback")
def submit_divination_feedback(
    record_id: int,
    req: DivinationFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """占卜反馈（允许修改）"""
    record = (
        db.query(DivinationRecord)
        .filter(
            DivinationRecord.id == record_id,
            DivinationRecord.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="占卜记录不存在")

    record.user_rating = req.rating
    record.user_feedback_text = req.feedback_text
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "data": _record_to_list_dict(record),
    }


# --- 辅助函数 ---

def _record_to_list_dict(r: DivinationRecord) -> dict:
    """占卜记录转列表字典"""
    summary = ""
    if r.question:
        summary = r.question[:30] + "..." if len(r.question) > 30 else r.question

    return {
        "id": r.id,
        "type": r.type,
        "question": r.question,
        "summary": summary,
        "user_rating": r.user_rating,
        "user_feedback_text": r.user_feedback_text,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
