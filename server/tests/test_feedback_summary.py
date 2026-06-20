# -*- coding: utf-8 -*-
"""Spec 015: 用户反馈摘要测试"""
import pytest
from datetime import date, datetime, timezone

from app.models.daily_fortune import DailyFortune
from app.models.divination_record import DivinationRecord
from app.services.feedback_summary import generate_feedback_summary


def _create_user(db):
    """创建测试用户"""
    from app.models.user import User
    from app.core.security import hash_password
    user = User(
        username="feedback_user",
        email="feedback@test.com",
        password_hash=hash_password("Pass1234"),
        birth_year=1990, birth_month=6, birth_day=15,
        birth_hour=8, gender=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_fortune_feedback(db, user_id, rating, tags=None, text="", d=None):
    """添加带反馈的每日运势"""
    row = DailyFortune(
        user_id=user_id,
        date=d or date(2026, 6, 1),
        heavenly_stem="甲", earthly_branch="子",
        overall_score=75,
        user_rating=rating,
        user_feedback_tags=tags,
        user_feedback_text=text,
    )
    db.add(row)
    db.commit()
    return row


def _add_divination_feedback(db, user_id, rating, text=""):
    """添加带反馈的占卜记录"""
    row = DivinationRecord(
        user_id=user_id,
        type="liuyao",
        question="事业如何",
        user_rating=rating,
        user_feedback_text=text,
    )
    db.add(row)
    db.commit()
    return row


class TestFeedbackSummary:
    """generate_feedback_summary"""

    def test_no_feedback_returns_default(self, db_session):
        """无反馈返回默认文本"""
        user = _create_user(db_session)
        result = generate_feedback_summary(db_session, user.id)
        assert result == "暂无用户反馈数据"

    def test_with_fortune_feedback(self, db_session):
        """有运势反馈时生成摘要"""
        user = _create_user(db_session)
        _add_fortune_feedback(
            db_session, user.id, rating=4,
            tags=["准确", "详细"], text="财运分析很好",
            d=date(2026, 6, 1),
        )
        _add_fortune_feedback(
            db_session, user.id, rating=5,
            tags=["准确"], text="事业运很准",
            d=date(2026, 6, 2),
        )

        result = generate_feedback_summary(db_session, user.id)

        assert "运势反馈" in result
        assert "平均评分" in result
        assert "4.5" in result  # (4+5)/2 = 4.5

    def test_dimension_preference(self, db_session):
        """从反馈文本中提取维度偏好"""
        user = _create_user(db_session)
        for i in range(5):
            _add_fortune_feedback(
                db_session, user.id, rating=4,
                text="财运分析很准，希望更详细",
                d=date(2026, 6, i + 1),
            )

        result = generate_feedback_summary(db_session, user.id)
        assert "财运" in result

    def test_tag_statistics(self, db_session):
        """标签统计"""
        user = _create_user(db_session)
        for i in range(3):
            _add_fortune_feedback(
                db_session, user.id, rating=4,
                tags=["准确", "简洁"],
                d=date(2026, 6, i + 1),
            )

        result = generate_feedback_summary(db_session, user.id)
        assert "准确" in result

    def test_divination_feedback(self, db_session):
        """占卜反馈"""
        user = _create_user(db_session)
        _add_divination_feedback(db_session, user.id, rating=3)
        _add_divination_feedback(db_session, user.id, rating=4)

        result = generate_feedback_summary(db_session, user.id)
        assert "占卜反馈" in result
        assert "3.5" in result

    def test_mixed_feedback(self, db_session):
        """混合反馈"""
        user = _create_user(db_session)
        _add_fortune_feedback(
            db_session, user.id, rating=5,
            tags=["准确"], text="感情运分析到位",
            d=date(2026, 6, 1),
        )
        _add_divination_feedback(db_session, user.id, rating=4)

        result = generate_feedback_summary(db_session, user.id)
        assert "运势反馈" in result
        assert "占卜反馈" in result

    def test_summary_length_limit(self, db_session):
        """摘要不超过 200 字"""
        user = _create_user(db_session)
        for i in range(30):
            _add_fortune_feedback(
                db_session, user.id, rating=4,
                tags=["标签" + str(j) for j in range(10)],
                text="反馈内容" * 20,
                d=date(2026, 1, 1) + __import__("datetime").timedelta(days=i),
            )

        result = generate_feedback_summary(db_session, user.id)
        assert len(result) <= 200
