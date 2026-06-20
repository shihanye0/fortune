# -*- coding: utf-8 -*-
"""配置管理测试"""
import os


def test_config_reads_database_url():
    """配置应能读取 DATABASE_URL 环境变量"""
    os.environ["DATABASE_URL"] = "mysql+pymysql://test:test@localhost:3306/test_db"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["DEEPSEEK_API_KEY"] = "sk-test"

    from app.config import settings

    assert settings.DATABASE_URL == "mysql+pymysql://test:test@localhost:3306/test_db"

    # 清理
    del os.environ["DATABASE_URL"]
    del os.environ["JWT_SECRET"]
    del os.environ["DEEPSEEK_API_KEY"]


def test_config_has_default_values():
    """配置应有合理的默认值"""
    os.environ["DATABASE_URL"] = "mysql+pymysql://test:test@localhost:3306/test_db"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["DEEPSEEK_API_KEY"] = "sk-test"

    from app.config import settings

    assert settings.APP_PORT == 8000
    assert settings.JWT_EXPIRE_HOURS == 24
    assert settings.SMTP_HOST == "smtp.qq.com"

    # 清理
    del os.environ["DATABASE_URL"]
    del os.environ["JWT_SECRET"]
    del os.environ["DEEPSEEK_API_KEY"]
