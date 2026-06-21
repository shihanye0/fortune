# -*- coding: utf-8 -*-
"""占卜记录模型"""
from sqlalchemy import JSON, BIGINT, BOOLEAN, SMALLINT, String, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DivinationRecord(TimestampMixin, Base):
    """占卜记录表"""

    __tablename__ = "divination_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT, nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="liuyao/qimen"
    )
    question: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    llm_interpretation: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # 用户反馈
    user_rating: Mapped[int | None] = mapped_column(SMALLINT, nullable=True)
    user_feedback_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # 准确性标记：1=准, 0=不准, null=未标记
    accuracy_mark: Mapped[int | None] = mapped_column(
        SMALLINT, nullable=True, default=None,
        comment="准确性标记: 1=准, 0=不准, null=未标记"
    )
    # 事件是否被验证
    outcome_verified: Mapped[bool | None] = mapped_column(
        BOOLEAN, nullable=True, default=None,
        comment="事件是否被验证"
    )
