# -*- coding: utf-8 -*-
"""用户模型"""
from sqlalchemy import BIGINT, BOOLEAN, INT, SMALLINT, String, TIME
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

    # LLM 配置
    llm_provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="LLM供应商名称"
    )
    llm_notes: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="LLM配置备注"
    )
    llm_website: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="LLM供应商官网"
    )
    llm_api_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="LLM API Key"
    )
    llm_api_key_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="获取API Key的链接"
    )
    llm_api_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="LLM API URL"
    )
    llm_model: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="LLM模型名称"
    )
