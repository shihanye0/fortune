# -*- coding: utf-8 -*-
"""配置管理测试"""


def test_config_reads_database_url():
    """配置应能读取 DATABASE_URL 环境变量"""
    from app.config import settings

    # conftest 设置了 sqlite:///test.db
    assert settings.DATABASE_URL is not None
    assert len(settings.DATABASE_URL) > 0


def test_config_has_default_values():
    """配置应有合理的默认值"""
    from app.config import settings

    assert settings.APP_PORT == 8080
    assert settings.JWT_EXPIRE_HOURS == 24
    assert settings.SMTP_HOST == "smtp.qq.com"
