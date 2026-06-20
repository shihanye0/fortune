# -*- coding: utf-8 -*-
"""用户登录 API 测试"""
import os

os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["DEEPSEEK_API_KEY"] = "sk-test"

REGISTER_DATA = {
    "username": "张三",
    "email": "zhangsan@qq.com",
    "password": "Abc123456",
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 8,
    "gender": 1,
}


def test_login_success(client):
    """使用正确凭据登录应返回 Token"""
    client.post("/api/v1/auth/register", json=REGISTER_DATA)

    response = client.post("/api/v1/auth/login", json={
        "email": "zhangsan@qq.com",
        "password": "Abc123456",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert len(data["data"]["token"]) > 0


def test_login_wrong_password(client):
    """密码错误应返回 401"""
    client.post("/api/v1/auth/register", json=REGISTER_DATA)

    response = client.post("/api/v1/auth/login", json={
        "email": "zhangsan@qq.com",
        "password": "wrong_password",
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "邮箱或密码错误" in data["error"]["message"]


def test_login_nonexistent_email(client):
    """邮箱不存在应返回 401（不暴露邮箱是否存在）"""
    response = client.post("/api/v1/auth/login", json={
        "email": "notexist@qq.com",
        "password": "Abc123456",
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "邮箱或密码错误" in data["error"]["message"]
