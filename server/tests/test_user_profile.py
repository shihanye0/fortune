# -*- coding: utf-8 -*-
"""Spec 006: 个人信息管理测试"""
import pytest


def _register_and_login(client):
    """辅助：注册并登录，返回 token"""
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "profile@test.com",
        "password": "Pass1234",
        "birth_year": 1990, "birth_month": 6, "birth_day": 15,
        "birth_hour": 8, "gender": 1,
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "profile@test.com",
        "password": "Pass1234",
    })
    return res.json()["data"]["token"]


class TestGetProfile:
    """GET /api/v1/users/me"""

    def test_get_profile_success(self, client):
        """已登录用户能查看个人信息"""
        token = _register_and_login(client)
        res = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["email"] == "profile@test.com"
        assert data["data"]["birth_year"] == 1990
        assert data["data"]["birth_hour"] == 8
        assert "password" not in data["data"]
        assert "password_hash" not in data["data"]

    def test_get_profile_no_token(self, client):
        """未登录返回 401"""
        res = client.get("/api/v1/users/me")
        assert res.status_code == 401

    def test_get_profile_invalid_token(self, client):
        """无效 token 返回 401"""
        res = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert res.status_code == 401


class TestUpdateProfile:
    """PUT /api/v1/users/me"""

    def test_update_username(self, client):
        """修改用户名"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me",
            json={"username": "newname"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["username"] == "newname"

    def test_update_username_invalid(self, client):
        """用户名为空返回 422"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me",
            json={"username": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422


class TestUpdateBirth:
    """PUT /api/v1/users/me/birth"""

    def test_update_birth_info(self, client):
        """修改生辰信息"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/birth",
            json={
                "birth_year": 1995, "birth_month": 3,
                "birth_day": 20, "birth_hour": 10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["birth_year"] == 1995
        assert data["data"]["birth_hour"] == 10

    def test_update_birth_invalid_date(self, client):
        """无效日期返回 422"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/birth",
            json={
                "birth_year": 1990, "birth_month": 13,
                "birth_day": 1, "birth_hour": 0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422
