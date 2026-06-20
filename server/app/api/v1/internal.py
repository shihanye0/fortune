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

    # 查询匹配小时的开启用户
    # push_time 格式 "HH:MM"，匹配前两位
    users = (
        db.query(User)
        .filter(User.push_enabled.is_(True))
        .all()
    )
    # Python 层过滤小时匹配
    target_users = [u for u in users if u.push_time and u.push_time[:2] == f"{req.hour:02d}"]

    today = date.today()
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

            # 3. LLM 解读（降级处理）
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

            # 4. 构建运势数据
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
            }

            # 5. 推送
            push_ok = False
            if user.push_channel in ("email", "both"):
                if send_fortune_email(user.email, fortune_data):
                    push_ok = True

            if user.push_channel in ("feishu", "both") and user.feishu_webhook:
                if send_fortune_feishu(user.feishu_webhook, fortune_data):
                    push_ok = True

            # 6. 存入数据库
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
