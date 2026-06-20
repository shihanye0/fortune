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


# --- Spec 007: 推送设置 ---


class TestPushSettings:
    """PUT /api/v1/users/me/push-settings"""

    def test_enable_push(self, client):
        """开启推送"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={
                "push_enabled": True,
                "push_channel": "email",
                "push_time": "07:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["push_enabled"] is True
        assert data["data"]["push_channel"] == "email"
        assert data["data"]["push_time"] == "07:00"

    def test_disable_push(self, client):
        """关闭推送"""
        token = _register_and_login(client)
        client.put(
            "/api/v1/users/me/push-settings",
            json={"push_enabled": True, "push_channel": "email", "push_time": "07:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={"push_enabled": False, "push_channel": "email", "push_time": "07:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["push_enabled"] is False

    def test_set_feishu_channel(self, client):
        """设置飞书推送"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={
                "push_enabled": True,
                "push_channel": "feishu",
                "push_time": "08:00",
                "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/abc123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["push_channel"] == "feishu"
        assert "feishu.cn" in data["feishu_webhook"]

    def test_feishu_without_webhook_rejected(self, client):
        """飞书推送无 Webhook 应拒绝"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={
                "push_enabled": True,
                "push_channel": "feishu",
                "push_time": "08:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "webhook" in res.json()["detail"].lower()

    def test_set_both_channel(self, client):
        """设置双渠道推送"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={
                "push_enabled": True,
                "push_channel": "both",
                "push_time": "09:00",
                "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xyz",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["push_channel"] == "both"

    def test_push_time_format(self, client):
        """无效时间格式返回 422"""
        token = _register_and_login(client)
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={
                "push_enabled": True,
                "push_channel": "email",
                "push_time": "25:00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422

    def test_push_settings_no_auth(self, client):
        """未登录返回 401"""
        res = client.put(
            "/api/v1/users/me/push-settings",
            json={"push_enabled": True, "push_channel": "email", "push_time": "07:00"},
        )
        assert res.status_code == 401


# --- Spec 008: 账号注销 ---


class TestAccountDeletion:
    """DELETE /api/v1/users/me"""

    def test_delete_account_success(self, client):
        """正确密码注销账号"""
        token = _register_and_login(client)
        res = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "Pass1234"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # 注销后 token 失效
        res2 = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 401

    def test_delete_account_wrong_password(self, client):
        """密码错误无法注销"""
        token = _register_and_login(client)
        res = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "WrongPass1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "密码错误" in res.json()["detail"]

        # 账号仍存在
        res2 = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 200

    def test_delete_account_no_auth(self, client):
        """未登录返回 401"""
        res = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "Pass1234"},
        )
        assert res.status_code == 401
