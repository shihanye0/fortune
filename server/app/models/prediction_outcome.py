# -*- coding: utf-8 -*-
"""预测结果验证模型"""
from sqlalchemy import BIGINT, BOOLEAN, DateTime, ForeignKey, SMALLINT, String, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.base import Base, TimestampMixin


class PredictionOutcome(TimestampMixin, Base):
    """预测结果验证表

    记录用户对运势/占卜预测的实际反馈，用于追踪预测准确性。
    """

    __tablename__ = "prediction_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.id"), nullable=False, index=True
    )

    # 来源类型：fortune=每日运势, divination=占卜记录
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="来源类型: fortune=每日运势, divination=占卜记录"
    )
    # 来源记录 ID（关联 daily_fortunes.id 或 divination_records.id）
    source_id: Mapped[int] = mapped_column(
        BIGINT, nullable=False, index=True,
        comment="来源记录ID"
    )

    # 用户描述的事件结果
    outcome_text: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    # 是否确实发生
    verified: Mapped[bool | None] = mapped_column(
        BOOLEAN, nullable=True, default=None,
        comment="事件是否确实发生"
    )
    # 验证时间
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="验证时间"
    )
