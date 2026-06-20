# -*- coding: utf-8 -*-
"""数据库模型测试"""
from datetime import datetime


def test_user_model_fields():
    """用户模型应包含所有必要字段"""
    from app.models.user import User

    user = User(
        username="张三",
        email="zhangsan@qq.com",
        password_hash="hashed_password",
        birth_year=1990,
        birth_month=5,
        birth_day=15,
        birth_hour=8,
        gender=1,
        birth_location="北京",
        push_channel="email",
        push_enabled=True,
        push_time="07:00",
    )

    assert user.username == "张三"
    assert user.email == "zhangsan@qq.com"
    assert user.birth_year == 1990
    assert user.birth_month == 5
    assert user.birth_day == 15
    assert user.birth_hour == 8
    assert user.gender == 1
    assert user.push_channel == "email"
    assert user.push_enabled is True


def test_user_model_table_name():
    """用户模型表名应为 users"""
    from app.models.user import User

    assert User.__tablename__ == "users"


def test_bazi_profile_model():
    """八字档案模型应包含四柱和五行数据"""
    from app.models.bazi_profile import BaziProfile

    profile = BaziProfile(
        user_id=1,
        year_pillar="庚午",
        month_pillar="辛巳",
        day_pillar="丙寅",
        hour_pillar="壬辰",
        day_master="丙",
        five_elements={"金": 2, "木": 1, "水": 1, "火": 2, "土": 2},
    )

    assert profile.year_pillar == "庚午"
    assert profile.day_master == "丙"
    assert profile.five_elements["金"] == 2
    assert BaziProfile.__tablename__ == "bazi_profiles"


def test_daily_fortune_model():
    """每日运势模型应包含评分和解读"""
    from app.models.daily_fortune import DailyFortune

    fortune = DailyFortune(
        user_id=1,
        date="2026-06-20",
        heavenly_stem="甲",
        earthly_branch="子",
        overall_score=4,
        lucky_color="红色",
    )

    assert fortune.overall_score == 4
    assert fortune.lucky_color == "红色"
    assert DailyFortune.__tablename__ == "daily_fortunes"


def test_divination_record_model():
    """占卜记录模型应包含类型和问题"""
    from app.models.divination_record import DivinationRecord

    record = DivinationRecord(
        user_id=1,
        type="liuyao",
        question="最近工作是否顺利",
    )

    assert record.type == "liuyao"
    assert record.question == "最近工作是否顺利"
    assert DivinationRecord.__tablename__ == "divination_records"
