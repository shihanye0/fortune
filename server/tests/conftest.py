# -*- coding: utf-8 -*-
"""测试配置：SQLite 内存数据库 + FastAPI TestClient"""
import os

os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["DEEPSEEK_API_KEY"] = "sk-test"
os.environ["INTERNAL_API_KEY"] = "test-internal-api-key"
os.environ["LLM_CREDENTIAL_ENCRYPTION_KEY"] = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.models.base import Base

# 确保所有模型被导入，create_all 才能创建所有表
from app.models.user import User  # noqa
from app.models.bazi_profile import BaziProfile  # noqa
from app.models.daily_fortune import DailyFortune  # noqa
from app.models.divination_record import DivinationRecord  # noqa
from app.models.probability_event_feedback import ProbabilityEventFeedback  # noqa
from app.models.push_delivery import PushDelivery  # noqa


@pytest.fixture(scope="function")
def db_session():
    """每个测试函数独立的 SQLite 内存数据库"""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 启用外键约束
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """FastAPI TestClient，使用测试数据库"""
    from app.api.deps import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
