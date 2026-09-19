# -*- coding: utf-8 -*-
"""配置管理"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    DATABASE_URL: str

    # LLM API（字段名为兼容既有环境变量，默认供应商为 DeepSeek）
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    # 仅允许服务端主动访问受信任的 LLM API，避免用户配置被当作 SSRF 跳板。
    LLM_ALLOWED_HOSTS: str = "api.deepseek.com,api.xiaomimimo.com"
    # Fernet key。未配置时仍可使用服务器默认 DeepSeek，但拒绝保存个人 API Key。
    LLM_CREDENTIAL_ENCRYPTION_KEY: str = ""

    # QQ 邮箱 SMTP
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # JWT
    JWT_SECRET: str
    JWT_EXPIRE_HOURS: int = 24

    # GitHub Actions 调用每日推送内部接口时使用的共享密钥。
    INTERNAL_API_KEY: str = ""

    # 应用配置
    APP_PORT: int = 8000
    APP_ENV: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
