# -*- coding: utf-8 -*-
"""SQLAlchemy 基础模型"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))


def china_now() -> datetime:
    """返回中国时区的当前时间"""
    return datetime.now(CHINA_TZ)


def utc_now() -> datetime:
    """返回UTC时间"""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """时间戳混入"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=china_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=china_now,
        onupdate=china_now,
        nullable=False,
    )
