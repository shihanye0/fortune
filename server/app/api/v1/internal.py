# -*- coding: utf-8 -*-
"""Spec 018: 每日推送调度内部接口"""
import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.models.daily_fortune import DailyFortune
from app.core.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["内部接口"])


class DailyPushRequest(BaseModel):
    hour: int  # 当前小时 (0-23)


@router.post("/daily-push")
def daily_push(req: DailyPushRequest, db: Session = Depends(get_db)):
    """每日运势推送调度

    GitHub Actions 每小时触发，推送 push_time 匹配当前小时的用户。
    """
    from fortune_engine.bazi.pillar import calculate_bazi
    from fortune_engine.bazi.daily_fortune import calculate_daily_fortune
    from fortune_engine.services.deepseek import interpret_daily, FALLBACK_DAILY
    from app.services.feedback_summary import generate_feedback_summary
    from app.services.push_email import send_fortune_email
    from app.services.push_feishu import send_fortune_feishu

    target_time = f"{req.hour:02d}:00"

    # 查询所有开启推送的用户
    users = (
        db.query(User)
        .filter(User.push_enabled.is_(True))
        .all()
    )

    # 分两类用户：
    # 1. 正常推送：push_time 匹配当前小时
    # 2. 补推：今日还没推送过，且当前时间已过其 push_time
    target_user_ids = set()
    target_users = []
    today = date.today()

    for u in users:
        if not u.push_time:
            continue

        push_hour = u.push_time[:2]
        current_hour = f"{req.hour:02d}"

        # 正常推送：小时匹配
        if push_hour == current_hour:
            target_users.append(u)
            target_user_ids.add(u.id)
            continue

        # 补推：当前时间已过其 push_time，且今日未推送
        if int(current_hour) > int(push_hour) and u.id not in target_user_ids:
            already_pushed = (
                db.query(DailyFortune.id)
                .filter(DailyFortune.user_id == u.id, DailyFortune.date == today)
                .first()
            )
            if not already_pushed:
                target_users.append(u)
                target_user_ids.add(u.id)
                logger.info("补推用户 user=%d, 原定时间 %s, 当前 %s", u.id, u.push_time, target_time)

    pushed_count = 0
    failed_count = 0

    for user in target_users:
        try:
            # 1. 计算八字
            bazi_result = calculate_bazi(
                user.birth_year, user.birth_month, user.birth_day,
                user.birth_hour, user.gender,
            )

            # 2. 计算今日运势
            daily = calculate_daily_fortune(bazi_result, today.year, today.month, today.day)

            # 3. 计算时辰运势
            from fortune_engine.bazi.hourly_fortune import calculate_all_hours_fortune
            hourly_fortunes = calculate_all_hours_fortune(bazi_result, today.year, today.month, today.day)

            # 4. 生成概率事件
            from fortune_engine.probability_events import generate_probability_events
            feedback_summary_text = generate_feedback_summary(db, user.id)
            probability_events = generate_probability_events(
                bazi_result, daily, hourly_fortunes, today, feedback_summary_text,
            )

            # 5. LLM 解读（降级处理）
            bazi_summary = (
                f"八字：{bazi_result['year_pillar']} {bazi_result['month_pillar']} "
                f"{bazi_result['day_pillar']} {bazi_result['hour_pillar']}，"
                f"日主：{bazi_result['day_master']}，"
                f"喜用神：{'、'.join(bazi_result.get('favorable_elements', []))}"
            )

            try:
                interpretation = interpret_daily(bazi_summary, daily, feedback_summary_text)
            except Exception as e:
                logger.error("LLM 解读失败 user=%d: %s", user.id, e)
                interpretation = FALLBACK_DAILY

            # 6. 构建完整运势数据
            fortune_data = {
                "date": today.isoformat(),
                "overall_score": daily["overall_score"],
                "career": daily.get("career_fortune", {}),
                "wealth": daily.get("wealth_fortune", {}),
                "love": daily.get("love_fortune", {}),
                "health": daily.get("health_fortune", {}),
                "lucky_color": daily.get("lucky_color", ""),
                "lucky_number": daily.get("lucky_number", ""),
                "lucky_direction": daily.get("lucky_direction", ""),
                "interpretation": interpretation,
                "hourly_fortunes": hourly_fortunes,
                "probability_events": probability_events,
            }

            # 7. 推送
            push_ok = False
            if user.push_channel in ("email", "both"):
                if send_fortune_email(user.email, fortune_data):
                    push_ok = True

            if user.push_channel in ("feishu", "both") and user.feishu_webhook:
                if send_fortune_feishu(user.feishu_webhook, fortune_data):
                    push_ok = True

            # 8. 存入数据库
            row = DailyFortune(
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
                hourly_fortunes=hourly_fortunes,
                llm_interpretation=interpretation,
            )
            db.add(row)
            db.commit()

            if push_ok:
                pushed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error("推送失败 user=%d: %s", user.id, e)
            db.rollback()
            failed_count += 1

    return {
        "success": True,
        "data": {
            "target_hour": req.hour,
            "total_users": len(target_users),
            "pushed_count": pushed_count,
            "failed_count": failed_count,
        },
    }
