# -*- coding: utf-8 -*-
"""每日推送的可恢复投递记录。"""
from datetime import date, datetime

from sqlalchemy import BIGINT, DATE, JSON, SMALLINT, String, TEXT, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PushDelivery(TimestampMixin, Base):
    """以用户、日期和渠道为幂等键的推送 outbox。"""

    __tablename__ = "push_deliveries"
    __table_args__ = (
        UniqueConstraint("user_id", "date", "channel", name="uq_push_delivery_user_date_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(DATE, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    attempts: Mapped[int] = mapped_column(SMALLINT, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
