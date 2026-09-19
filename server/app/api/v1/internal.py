# -*- coding: utf-8 -*-
"""每日推送调度内部接口。"""
import logging
import secrets
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.models.base import CHINA_TZ
from app.models.daily_fortune import DailyFortune
from app.models.push_delivery import PushDelivery
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["内部接口"])


class DailyPushRequest(BaseModel):
    hour: int = Field(..., ge=0, le=23)


def require_internal_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """阻止公开接口被伪造调度请求触发批量推送。"""
    expected = settings.INTERNAL_API_KEY.strip()
    if not expected:
        logger.error("未配置 INTERNAL_API_KEY，拒绝执行每日推送")
        raise HTTPException(status_code=503, detail="内部推送密钥尚未配置")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="内部推送认证失败")


def _configured_channels(user: User) -> tuple[str, ...]:
    if user.push_channel == "email":
        return ("email",)
    if user.push_channel == "feishu" and user.feishu_webhook:
        return ("feishu",)
    if user.push_channel == "both":
        return tuple(
            channel
            for channel, enabled in (("email", bool(user.email)), ("feishu", bool(user.feishu_webhook)))
            if enabled
        )
    return ()


def _generate_fortune(user: User, today: date, db: Session) -> DailyFortune:
    """先持久化日运，再为每个渠道创建独立投递任务。"""
    existing = (
        db.query(DailyFortune)
        .filter(DailyFortune.user_id == user.id, DailyFortune.date == today)
        .order_by(DailyFortune.id.desc())
        .first()
    )
    if existing:
        return existing

    from app.services.feedback_summary import generate_feedback_summary
    from fortune_engine.bazi.daily_fortune import calculate_daily_fortune
    from fortune_engine.bazi.hourly_fortune import calculate_all_hours_fortune
    from fortune_engine.bazi.pillar import calculate_bazi
    from fortune_engine.services.deepseek import (
        FALLBACK_DAILY,
        get_user_llm_overrides,
        interpret_daily,
    )

    bazi = calculate_bazi(
        user.birth_year, user.birth_month, user.birth_day, user.birth_hour, user.gender,
    )
    daily = calculate_daily_fortune(bazi, today.year, today.month, today.day)
    hourly = calculate_all_hours_fortune(bazi, today.year, today.month, today.day)
    feedback_summary = generate_feedback_summary(db, user.id)
    bazi_summary = (
        f"八字：{bazi['year_pillar']} {bazi['month_pillar']} {bazi['day_pillar']} {bazi['hour_pillar']}，"
        f"日主：{bazi['day_master']}，喜用神：{'、'.join(bazi.get('favorable_elements', []))}"
    )
    try:
        interpretation = interpret_daily(
            bazi_summary, daily, feedback_summary, **get_user_llm_overrides(user),
        )
    except Exception as exc:
        logger.error("推送 LLM 解读失败 user=%d: %s", user.id, type(exc).__name__)
        interpretation = FALLBACK_DAILY

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
        hourly_fortunes=hourly,
        llm_interpretation=interpretation,
    )
    db.add(fortune)
    db.commit()
    db.refresh(fortune)
    return fortune


def _build_payload(
    user: User,
    fortune: DailyFortune,
    today: date,
    current_hour: int,
    db: Session,
) -> dict:
    """创建可重试的冻结内容，避免重试时悄悄改变当天的推送文本。"""
    from app.services.feedback_summary import generate_feedback_summary
    from fortune_engine.bazi.daily_fortune import calculate_daily_fortune
    from fortune_engine.bazi.pillar import calculate_bazi
    from fortune_engine.probability_events import generate_probability_events

    bazi = calculate_bazi(
        user.birth_year, user.birth_month, user.birth_day, user.birth_hour, user.gender,
    )
    daily = calculate_daily_fortune(bazi, today.year, today.month, today.day)
    probability_events = generate_probability_events(
        bazi,
        daily,
        fortune.hourly_fortunes or [],
        today,
        generate_feedback_summary(db, user.id),
        current_hour=current_hour,
    )
    return {
        "date": today.isoformat(),
        "day_ganzhi": f"{fortune.heavenly_stem or ''}{fortune.earthly_branch or ''}",
        "overall_score": fortune.overall_score,
        "career": fortune.career_fortune or {},
        "wealth": fortune.wealth_fortune or {},
        "love": fortune.love_fortune or {},
        "health": fortune.health_fortune or {},
        "lucky_color": fortune.lucky_color or "",
        "lucky_number": fortune.lucky_number or "",
        "lucky_direction": fortune.lucky_direction or "",
        "interpretation": fortune.llm_interpretation or "",
        "hourly_fortunes": fortune.hourly_fortunes or [],
        "probability_events": probability_events,
        "calculation_notice": "传统文化参考，不构成医疗、法律或投资建议。",
    }


def _create_deliveries(user: User, today: date, payload: dict, now: datetime, db: Session) -> list[PushDelivery]:
    """用数据库唯一键保证同一渠道每天最多产生一条待投递任务。"""
    created: list[PushDelivery] = []
    for channel in _configured_channels(user):
        row = (
            db.query(PushDelivery)
            .filter(
                PushDelivery.user_id == user.id,
                PushDelivery.date == today,
                PushDelivery.channel == channel,
            )
            .first()
        )
        if row:
            continue
        row = PushDelivery(
            user_id=user.id,
            date=today,
            channel=channel,
            status="pending",
            payload=payload,
            next_attempt_at=now,
        )
        try:
            # 每条投递使用 savepoint；并发的同键请求只会让其中一方创建成功。
            with db.begin_nested():
                db.add(row)
                db.flush()
            created.append(row)
        except IntegrityError:
            logger.info("推送任务已由并发请求创建 user=%d channel=%s", user.id, channel)
    if created:
        db.commit()
        for row in created:
            db.refresh(row)
    return created


def _record_delivery_result(delivery: PushDelivery, success: bool, now: datetime, db: Session) -> bool:
    delivery.attempts += 1
    if success:
        delivery.status = "delivered"
        delivery.delivered_at = now
        delivery.next_attempt_at = None
        delivery.last_error = None
    else:
        # 5 分钟起步，指数退避到 6 小时；不因一次错误丢弃用户的推送意图。
        minutes = min(360, 5 * (2 ** max(0, delivery.attempts - 1)))
        delivery.status = "pending"
        delivery.next_attempt_at = now + timedelta(minutes=minutes)
        delivery.last_error = "渠道未确认接收，将自动重试"
    db.commit()
    return success


def _deliver(delivery: PushDelivery, user: User, now: datetime, db: Session) -> bool:
    """只发送一条 outbox 任务；email 与飞书互不影响。"""
    from app.services.push_email import send_fortune_email
    from app.services.push_feishu import send_fortune_feishu

    try:
        if delivery.channel == "email":
            success = send_fortune_email(user.email, delivery.payload)
        elif delivery.channel == "feishu" and user.feishu_webhook:
            success = send_fortune_feishu(user.feishu_webhook, delivery.payload)
        else:
            success = False
    except Exception as exc:
        logger.error("推送异常 delivery=%d: %s", delivery.id, type(exc).__name__)
        success = False
    return _record_delivery_result(delivery, success, now, db)


def _is_due_for_user(user: User, hour: int) -> bool:
    if not user.push_enabled or not user.push_time:
        return False
    return hour >= int(user.push_time[:2])


@router.post("/daily-push")
def daily_push(
    req: DailyPushRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_api_key),
):
    """创建当天渠道 outbox，并重试此前未投递成功的渠道。"""
    now = datetime.now(CHINA_TZ)
    today = now.date()
    target_users = [
        user for user in db.query(User).filter(User.push_enabled.is_(True)).all()
        if _is_due_for_user(user, req.hour)
    ]

    pending: list[tuple[PushDelivery, User]] = list(
        db.query(PushDelivery, User)
        .join(User, User.id == PushDelivery.user_id)
        .filter(
            PushDelivery.status == "pending",
            PushDelivery.next_attempt_at.isnot(None),
            PushDelivery.next_attempt_at <= now,
            User.push_enabled.is_(True),
        )
        .all()
    )
    pending_ids = {delivery.id for delivery, _user in pending}
    generation_failures = 0

    for user in target_users:
        try:
            fortune = _generate_fortune(user, today, db)
            payload = _build_payload(user, fortune, today, now.hour, db)
            for delivery in _create_deliveries(user, today, payload, now, db):
                if delivery.id not in pending_ids:
                    pending.append((delivery, user))
                    pending_ids.add(delivery.id)
        except Exception as exc:
            logger.error("创建推送任务失败 user=%d: %s", user.id, type(exc).__name__)
            db.rollback()
            generation_failures += 1

    delivered_count = 0
    retry_count = 0
    for delivery, user in pending:
        if _deliver(delivery, user, now, db):
            delivered_count += 1
        else:
            retry_count += 1

    return {
        "success": True,
        "data": {
            "target_hour": req.hour,
            "total_users": len(target_users),
            "delivered_count": delivered_count,
            "retry_scheduled_count": retry_count,
            "generation_failed_count": generation_failures,
            # 兼容原调用方的字段语义：统计成功投递的渠道数。
            "pushed_count": delivered_count,
            "failed_count": generation_failures + retry_count,
        },
    }
