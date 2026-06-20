# -*- coding: utf-8 -*-
"""运势查看接口"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.users import get_current_user
from app.models.daily_fortune import DailyFortune
from app.models.user import User


router = APIRouter(prefix="/fortunes", tags=["运势查看"])


# --- Schema ---

class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    feedback_text: str | None = None


# --- 路由 ---

@router.get("/today")
def get_today_fortune(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看今日运势"""
    today = date.today()
    fortune = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.user_id == current_user.id,
            DailyFortune.date == today,
        )
        .first()
    )

    if not fortune:
        return {"success": True, "data": None, "message": "今日运势正在生成中，请稍后查看"}

    return {
        "success": True,
        "data": _fortune_to_detail_dict(fortune),
    }


@router.get("")
def list_fortunes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """历史运势列表"""
    offset = (page - 1) * limit

    total = (
        db.query(func.count(DailyFortune.id))
        .filter(DailyFortune.user_id == current_user.id)
        .scalar()
    )

    fortunes = (
        db.query(DailyFortune)
        .filter(DailyFortune.user_id == current_user.id)
        .order_by(DailyFortune.date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "success": True,
        "data": [_fortune_to_list_dict(f) for f in fortunes],
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    }


@router.get("/{fortune_id}")
def get_fortune_detail(
    fortune_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """运势详情"""
    fortune = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.id == fortune_id,
            DailyFortune.user_id == current_user.id,
        )
        .first()
    )

    if not fortune:
        raise HTTPException(status_code=404, detail="运势记录不存在")

    return {
        "success": True,
        "data": _fortune_to_detail_dict(fortune),
    }


@router.post("/{fortune_id}/feedback")
def submit_feedback(
    fortune_id: int,
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交反馈（允许修改）"""
    fortune = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.id == fortune_id,
            DailyFortune.user_id == current_user.id,
        )
        .first()
    )

    if not fortune:
        raise HTTPException(status_code=404, detail="运势记录不存在")

    fortune.user_rating = req.rating
    fortune.user_feedback_tags = req.tags
    fortune.user_feedback_text = req.feedback_text
    db.commit()
    db.refresh(fortune)

    return {
        "success": True,
        "data": _fortune_to_detail_dict(fortune),
    }


# --- 辅助函数 ---

def _fortune_to_detail_dict(f: DailyFortune) -> dict:
    """运势模型转详情字典"""
    return {
        "id": f.id,
        "date": f.date.isoformat() if f.date else None,
        "overall_score": f.overall_score,
        "career": f.career_fortune,
        "wealth": f.wealth_fortune,
        "love": f.love_fortune,
        "health": f.health_fortune,
        "lucky_color": f.lucky_color,
        "lucky_number": f.lucky_number,
        "lucky_direction": f.lucky_direction,
        "interpretation": f.llm_interpretation,
        "user_rating": f.user_rating,
        "user_feedback_tags": f.user_feedback_tags,
        "user_feedback_text": f.user_feedback_text,
    }


def _fortune_to_list_dict(f: DailyFortune) -> dict:
    """运势模型转列表字典（摘要）"""
    # 从 LLM 解读中截取摘要
    summary = ""
    if f.llm_interpretation:
        summary = f.llm_interpretation[:50] + "..." if len(f.llm_interpretation) > 50 else f.llm_interpretation

    return {
        "id": f.id,
        "date": f.date.isoformat() if f.date else None,
        "overall_score": f.overall_score,
        "summary": summary,
    }
