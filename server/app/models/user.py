# -*- coding: utf-8 -*-
"""用户模型"""
from sqlalchemy import BOOLEAN, INT, SMALLINT, String, TIME
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 生辰信息
    birth_year: Mapped[int] = mapped_column(INT, nullable=False)
    birth_month: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    birth_day: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    birth_hour: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    gender: Mapped[int] = mapped_column(SMALLINT, nullable=False, comment="0=女 1=男")
    birth_location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 推送设置
    push_channel: Mapped[str] = mapped_column(
        String(20), default="email", nullable=False
    )
    push_enabled: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    push_time: Mapped[str] = mapped_column(
        String(5), default="07:00", nullable=False
    )
    feishu_webhook: Mapped[str | None] = mapped_column(String(500), nullable=True)
