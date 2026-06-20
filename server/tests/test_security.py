# -*- coding: utf-8 -*-
"""安全模块测试：密码哈希和 JWT"""
import os

os.environ["DATABASE_URL"] = "mysql+pymysql://test:test@localhost:3306/test"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["DEEPSEEK_API_KEY"] = "sk-test"


def test_password_hash_and_verify():
    """密码哈希后应能正确验证"""
    from app.core.security import hash_password, verify_password

    password = "Abc123456"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation():
    """应能创建 JWT Token"""
    from app.core.security import create_access_token

    token = create_access_token(user_id=1)

    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_token_verification():
    """JWT Token 应能正确验证并返回 user_id"""
    from app.core.security import create_access_token, verify_token

    token = create_access_token(user_id=42)
    payload = verify_token(token)

    assert payload is not None
    assert payload["user_id"] == 42


def test_jwt_token_invalid():
    """无效 Token 应返回 None"""
    from app.core.security import verify_token

    payload = verify_token("invalid.token.here")

    assert payload is None
