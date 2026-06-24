# -*- coding: utf-8 -*-
"""概率事件反馈模型"""
from sqlalchemy import BIGINT, BOOLEAN, DATE, SMALLINT, String, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ProbabilityEventFeedback(TimestampMixin, Base):
    """概率事件反馈表"""

    __tablename__ = "probability_event_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)
    event_date: Mapped[str] = mapped_column(DATE, nullable=False, index=True)

    # 事件信息
    dimension: Mapped[str] = mapped_column(String(20), nullable=False, comment="事件维度")
    event_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="事件名称")
    probability: Mapped[int] = mapped_column(SMALLINT, nullable=False, comment="预测概率")

    # 反馈
    occurred: Mapped[bool | None] = mapped_column(
        BOOLEAN, nullable=True, default=None,
        comment="事件是否发生: null=未反馈, true=发生, false=未发生"
    )
    rating: Mapped[int | None] = mapped_column(
        SMALLINT, nullable=True, default=None,
        comment="准确度评分: 1-5"
    )
    feedback_text: Mapped[str | None] = mapped_column(TEXT, nullable=True, comment="反馈文字")
