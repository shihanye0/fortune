# -*- coding: utf-8 -*-
"""配置管理"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    DATABASE_URL: str

    # DeepSeek API
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # QQ 邮箱 SMTP
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # JWT
    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 24

    # 应用配置
    APP_PORT: int = 8000
    APP_ENV: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
