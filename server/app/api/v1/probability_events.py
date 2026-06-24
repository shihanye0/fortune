# -*- coding: utf-8 -*-
"""概率事件推算接口"""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.users import get_current_user
from app.models.user import User
from app.models.probability_event_feedback import ProbabilityEventFeedback

router = APIRouter(prefix="/probability-events", tags=["概率事件"])


class EventFeedbackRequest(BaseModel):
    """事件反馈请求"""
    dimension: str = Field(..., description="事件维度")
    event_name: str = Field(..., description="事件名称")
    probability: int = Field(..., description="预测概率")
    occurred: bool | None = Field(None, description="是否发生")
    rating: int | None = Field(None, ge=1, le=5, description="准确度评分 1-5")
    feedback_text: str | None = Field(None, description="反馈文字")


@router.get("/today")
def get_today_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日个性化概率事件"""
    from fortune_engine.bazi.pillar import calculate_bazi
    from fortune_engine.bazi.daily_fortune import calculate_daily_fortune
    from fortune_engine.bazi.hourly_fortune import calculate_all_hours_fortune
    from fortune_engine.probability_events import generate_probability_events

    today = date.today()

    # 1. 计算八字
    bazi = calculate_bazi(
        current_user.birth_year, current_user.birth_month,
        current_user.birth_day, current_user.birth_hour,
        current_user.gender,
    )

    # 2. 计算今日运势
    daily = calculate_daily_fortune(bazi, today.year, today.month, today.day)

    # 3. 计算时辰运势
    hourly = calculate_all_hours_fortune(bazi, today.year, today.month, today.day)

    # 4. 获取用户历史反馈摘要
    feedback_summary = _get_feedback_summary(db, current_user.id)

    # 5. 生成概率事件
    events = generate_probability_events(bazi, daily, hourly, today, feedback_summary)

    # 6. 标记已反馈的事件
    today_feedbacks = (
        db.query(ProbabilityEventFeedback)
        .filter(
            ProbabilityEventFeedback.user_id == current_user.id,
            ProbabilityEventFeedback.event_date == today,
        )
        .all()
    )
    feedback_map = {f"{f.dimension}:{f.event_name}": f for f in today_feedbacks}

    for event in events:
        key = f"{event['dimension']}:{event['event']}"
        fb = feedback_map.get(key)
        if fb:
            event["feedback"] = {
                "occurred": fb.occurred,
                "rating": fb.rating,
                "feedback_text": fb.feedback_text,
            }

    return {
        "success": True,
        "data": {
            "date": today.isoformat(),
            "events": events,
        },
    }


@router.post("/feedback")
def submit_event_feedback(
    req: EventFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交概率事件反馈"""
    today = date.today()

    # 查找是否已有反馈
    existing = (
        db.query(ProbabilityEventFeedback)
        .filter(
            ProbabilityEventFeedback.user_id == current_user.id,
            ProbabilityEventFeedback.event_date == today,
            ProbabilityEventFeedback.dimension == req.dimension,
            ProbabilityEventFeedback.event_name == req.event_name,
        )
        .first()
    )

    if existing:
        # 更新已有反馈
        existing.occurred = req.occurred
        existing.rating = req.rating
        existing.feedback_text = req.feedback_text
    else:
        # 创建新反馈
        feedback = ProbabilityEventFeedback(
            user_id=current_user.id,
            event_date=today,
            dimension=req.dimension,
            event_name=req.event_name,
            probability=req.probability,
            occurred=req.occurred,
            rating=req.rating,
            feedback_text=req.feedback_text,
        )
        db.add(feedback)

    db.commit()

    return {"success": True, "message": "反馈提交成功"}


@router.get("/feedback/history")
def get_feedback_history(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取概率事件反馈历史"""
    from sqlalchemy import func

    offset = (page - 1) * limit

    total = (
        db.query(func.count(ProbabilityEventFeedback.id))
        .filter(ProbabilityEventFeedback.user_id == current_user.id)
        .scalar()
    )

    records = (
        db.query(ProbabilityEventFeedback)
        .filter(ProbabilityEventFeedback.user_id == current_user.id)
        .order_by(ProbabilityEventFeedback.event_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "event_date": r.event_date.isoformat() if r.event_date else None,
                "dimension": r.dimension,
                "event_name": r.event_name,
                "probability": r.probability,
                "occurred": r.occurred,
                "rating": r.rating,
                "feedback_text": r.feedback_text,
            }
            for r in records
        ],
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    }


def _get_feedback_summary(db: Session, user_id: int) -> str:
    """获取用户历史反馈摘要"""
    from sqlalchemy import func

    # 统计反馈数据
    total = (
        db.query(func.count(ProbabilityEventFeedback.id))
        .filter(
            ProbabilityEventFeedback.user_id == user_id,
            ProbabilityEventFeedback.occurred.isnot(None),
        )
        .scalar()
    )

    if total == 0:
        return ""

    occurred_count = (
        db.query(func.count(ProbabilityEventFeedback.id))
        .filter(
            ProbabilityEventFeedback.user_id == user_id,
            ProbabilityEventFeedback.occurred == True,
        )
        .scalar()
    )

    avg_rating = (
        db.query(func.avg(ProbabilityEventFeedback.rating))
        .filter(
            ProbabilityEventFeedback.user_id == user_id,
            ProbabilityEventFeedback.rating.isnot(None),
        )
        .scalar()
    )

    # 各维度准确率
    dimension_stats = {}
    for dim in ["career", "wealth", "love", "health"]:
        dim_total = (
            db.query(func.count(ProbabilityEventFeedback.id))
            .filter(
                ProbabilityEventFeedback.user_id == user_id,
                ProbabilityEventFeedback.dimension == dim,
                ProbabilityEventFeedback.occurred.isnot(None),
            )
            .scalar()
        )
        if dim_total > 0:
            dim_occurred = (
                db.query(func.count(ProbabilityEventFeedback.id))
                .filter(
                    ProbabilityEventFeedback.user_id == user_id,
                    ProbabilityEventFeedback.dimension == dim,
                    ProbabilityEventFeedback.occurred == True,
                )
                .scalar()
            )
            dimension_stats[dim] = dim_occurred / dim_total

    summary = f"历史反馈{total}次，发生率{occurred_count/total:.0%}"
    if avg_rating:
        summary += f"，平均评分{avg_rating:.1f}"

    if dimension_stats:
        dim_str = "、".join(f"{d}={r:.0%}" for d, r in dimension_stats.items())
        summary += f"，各维度发生率：{dim_str}"

    return summary
