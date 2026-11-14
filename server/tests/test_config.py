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

    from pathlib import Path
    expected = 8000  # config.py 代码默认值；有 .env 时以 .env 为准
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for ln in env_file.read_text(encoding="utf-8").splitlines():
            if ln.startswith("APP_PORT="):
                expected = int(ln.split("=", 1)[1])
    assert settings.APP_PORT == expected
    assert settings.JWT_EXPIRE_HOURS == 24
    assert settings.SMTP_HOST == "smtp.qq.com"
