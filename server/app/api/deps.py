# -*- coding: utf-8 -*-
"""依赖注入"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
