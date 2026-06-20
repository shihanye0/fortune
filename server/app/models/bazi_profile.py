# -*- coding: utf-8 -*-
"""八字档案模型"""
from sqlalchemy import JSON, BIGINT, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BaziProfile(TimestampMixin, Base):
    """八字档案表"""

    __tablename__ = "bazi_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("users.id"), nullable=False
    )

    # 四柱
    year_pillar: Mapped[str] = mapped_column(String(4), nullable=False)
    month_pillar: Mapped[str] = mapped_column(String(4), nullable=False)
    day_pillar: Mapped[str] = mapped_column(String(4), nullable=False)
    hour_pillar: Mapped[str] = mapped_column(String(4), nullable=False)

    # 日主
    day_master: Mapped[str] = mapped_column(String(2), nullable=False)

    # 分析数据（JSON）
    five_elements: Mapped[dict] = mapped_column(JSON, nullable=False)
    ten_gods: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    major_luck_cycles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    favorable_elements: Mapped[list | None] = mapped_column(JSON, nullable=True)
