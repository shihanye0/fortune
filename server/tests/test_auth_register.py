# -*- coding: utf-8 -*-
"""用户注册 API 测试"""
import os

os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["DEEPSEEK_API_KEY"] = "sk-test"

VALID_REGISTER_DATA = {
    "username": "张三",
    "email": "zhangsan@qq.com",
    "password": "Abc123456",
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 8,
    "gender": 1,
    "birth_location": "北京",
}


def test_register_success(client):
    """使用有效信息注册应成功"""
    response = client.post("/api/v1/auth/register", json=VALID_REGISTER_DATA)

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "张三"
    assert data["data"]["email"] == "zhangsan@qq.com"
    assert "token" in data["data"]
    assert len(data["data"]["token"]) > 0


def test_register_duplicate_email(client):
    """邮箱已被注册应返回 409"""
    client.post("/api/v1/auth/register", json=VALID_REGISTER_DATA)

    response = client.post("/api/v1/auth/register", json=VALID_REGISTER_DATA)

    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert "已被注册" in data["error"]["message"]


def test_register_weak_password(client):
    """密码强度不足应返回 422"""
    invalid_data = {**VALID_REGISTER_DATA, "password": "123"}

    response = client.post("/api/v1/auth/register", json=invalid_data)

    assert response.status_code == 422


def test_register_invalid_email(client):
    """邮箱格式无效应返回 422"""
    invalid_data = {**VALID_REGISTER_DATA, "email": "not-an-email"}

    response = client.post("/api/v1/auth/register", json=invalid_data)

    assert response.status_code == 422


def test_register_missing_fields(client):
    """缺少必填字段应返回 422"""
    invalid_data = {"username": "张三"}

    response = client.post("/api/v1/auth/register", json=invalid_data)

    assert response.status_code == 422


def test_register_password_hashed(client, db_session):
    """密码应被哈希存储，不应存明文"""
    client.post("/api/v1/auth/register", json=VALID_REGISTER_DATA)

    from app.models.user import User

    user = db_session.query(User).filter(User.email == "zhangsan@qq.com").first()

    assert user is not None
    assert user.password_hash != "Abc123456"
    assert user.password_hash.startswith("$2b$")
