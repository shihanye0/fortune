# -*- coding: utf-8 -*-
"""初始化数据库表结构"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.deps import engine
from app.models.base import Base

# 导入所有模型以注册到 Base.metadata
from app.models.user import User  # noqa: F401
from app.models.bazi_profile import BaziProfile  # noqa: F401
from app.models.daily_fortune import DailyFortune  # noqa: F401
from app.models.divination_record import DivinationRecord  # noqa: F401


def init_db():
    """创建所有表"""
    print("[INFO] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created successfully")

    # 列出创建的表
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[INFO] Tables: {tables}")


if __name__ == "__main__":
    init_db()
