# -*- coding: utf-8 -*-
"""运势查看接口"""
from datetime import date, datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

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


class AccuracyMarkRequest(BaseModel):
    accuracy_mark: int = Field(..., ge=0, le=1, description="1=准, 0=不准")


# --- 路由 ---

@router.get("/today")
def get_today_fortune(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看今日运势（不存在时自动生成）"""
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
        # 按需生成今日运势
        fortune = _generate_fortune_on_demand(current_user, today, db)

    return {
        "success": True,
        "data": _fortune_to_detail_dict(fortune),
    }


@router.post("/today/regenerate")
def regenerate_today_fortune(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重新生成今日运势"""
    today = date.today()

    # 删除旧的运势记录
    old_fortune = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.user_id == current_user.id,
            DailyFortune.date == today,
        )
        .first()
    )

    if old_fortune:
        db.delete(old_fortune)
        db.commit()

    # 生成新的运势
    fortune = _generate_fortune_on_demand(current_user, today, db)

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


@router.post("/{fortune_id}/accuracy")
def mark_fortune_accuracy(
    fortune_id: int,
    req: AccuracyMarkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记运势准确性（1=准, 0=不准）"""
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

    fortune.accuracy_mark = req.accuracy_mark
    db.commit()
    db.refresh(fortune)

    return {
        "success": True,
        "data": _fortune_to_detail_dict(fortune),
    }


# --- 按需生成运势 ---

def _generate_fortune_on_demand(user: User, today: date, db: Session) -> DailyFortune:
    """用户查看今日运势时，如果不存在则自动生成"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # 1. 计算八字
        from fortune_engine.bazi.pillar import calculate_bazi
        bazi_result = calculate_bazi(
            user.birth_year, user.birth_month, user.birth_day,
            user.birth_hour, user.gender,
        )

        # 2. 计算今日运势
        from fortune_engine.bazi.daily_fortune import calculate_daily_fortune
        daily = calculate_daily_fortune(bazi_result, today.year, today.month, today.day)

        # 3. LLM 解读（降级处理）
        from fortune_engine.services.deepseek import interpret_daily, FALLBACK_DAILY
        from app.services.feedback_summary import generate_feedback_summary

        bazi_summary = (
            f"八字：{bazi_result['year_pillar']} {bazi_result['month_pillar']} "
            f"{bazi_result['day_pillar']} {bazi_result['hour_pillar']}，"
            f"日主：{bazi_result['day_master']}，"
            f"喜用神：{'、'.join(bazi_result.get('favorable_elements', []))}"
        )
        feedback_summary = generate_feedback_summary(db, user.id)

        try:
            interpretation = interpret_daily(bazi_summary, daily, feedback_summary)
        except Exception as e:
            logger.error("LLM 解读失败 user=%d: %s", user.id, e)
            interpretation = FALLBACK_DAILY

        # 4. 存入数据库
        fortune = DailyFortune(
            user_id=user.id,
            date=today,
            heavenly_stem=daily["heavenly_stem"],
            earthly_branch=daily["earthly_branch"],
            overall_score=daily["overall_score"],
            career_fortune=daily.get("career_fortune"),
            wealth_fortune=daily.get("wealth_fortune"),
            love_fortune=daily.get("love_fortune"),
            health_fortune=daily.get("health_fortune"),
            lucky_color=daily.get("lucky_color"),
            lucky_number=daily.get("lucky_number"),
            lucky_direction=daily.get("lucky_direction"),
            llm_interpretation=interpretation,
        )
        db.add(fortune)
        db.commit()
        db.refresh(fortune)

        logger.info("按需生成运势成功 user=%d date=%s", user.id, today)
        return fortune

    except Exception as e:
        logger.error("按需生成运势失败 user=%d: %s", user.id, e)
        db.rollback()
        # 返回一个默认运势，避免接口报错
        fortune = DailyFortune(
            user_id=user.id,
            date=today,
            heavenly_stem="甲",
            earthly_branch="子",
            overall_score=60,
            career_fortune={"score": 60, "description": "事业运势平稳"},
            wealth_fortune={"score": 60, "description": "财运一般"},
            love_fortune={"score": 60, "description": "感情运势平稳"},
            health_fortune={"score": 60, "description": "健康状况良好"},
            lucky_color="蓝色",
            lucky_number="3, 8",
            lucky_direction="东方",
            llm_interpretation="今日运势平稳，适合日常事务处理。",
        )
        db.add(fortune)
        db.commit()
        db.refresh(fortune)
        return fortune


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
        "accuracy_mark": f.accuracy_mark,
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
