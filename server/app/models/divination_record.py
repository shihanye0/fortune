# -*- coding: utf-8 -*-
"""占卜记录模型"""
from sqlalchemy import JSON, BIGINT, SMALLINT, String, TEXT
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
