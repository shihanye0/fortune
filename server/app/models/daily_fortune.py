# -*- coding: utf-8 -*-
"""每日运势模型"""
from sqlalchemy import JSON, BIGINT, DATE, SMALLINT, String, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DailyFortune(TimestampMixin, Base):
    """每日运势表"""

    __tablename__ = "daily_fortunes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT, nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(DATE, nullable=False)

    # 流日干支
    heavenly_stem: Mapped[str] = mapped_column(String(2), nullable=False)
    earthly_branch: Mapped[str] = mapped_column(String(2), nullable=False)

    # 运势评分
    overall_score: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    career_fortune: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    wealth_fortune: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    love_fortune: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    health_fortune: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 幸运信息
    lucky_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lucky_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lucky_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # LLM 解读
    llm_interpretation: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # 用户反馈
    user_rating: Mapped[int | None] = mapped_column(SMALLINT, nullable=True)
    user_feedback_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    user_feedback_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # 时辰运势（JSON 数组，包含 12 个时辰的运势）
    hourly_fortunes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 准确性标记：1=准, 0=不准, null=未标记
    accuracy_mark: Mapped[int | None] = mapped_column(
        SMALLINT, nullable=True, default=None,
        comment="准确性标记: 1=准, 0=不准, null=未标记"
    )
