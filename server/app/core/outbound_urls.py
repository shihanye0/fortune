"""服务端出站 URL 的最小安全边界。"""
from urllib.parse import urlparse


class OutboundUrlError(ValueError):
    """不允许服务端请求该 URL。"""


def normalize_https_url(value: str, *, allowed_hosts: set[str], field_name: str) -> str:
    """验证并规范化固定受信任主机上的 HTTPS URL。"""
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()

    if (
        parsed.scheme != "https"
        or not host
        or parsed.username
        or parsed.password
        or (parsed.port not in (None, 443))
        or host not in allowed_hosts
    ):
        raise OutboundUrlError(f"{field_name} 仅支持受信任服务商的 HTTPS 地址")
    return normalized


def normalize_feishu_webhook(value: str) -> str:
    """只接受飞书官方机器人 Webhook，防止用户输入触发任意出站请求。"""
    normalized = normalize_https_url(
        value,
        allowed_hosts={"open.feishu.cn"},
        field_name="飞书 Webhook",
    )
    if not urlparse(normalized).path.startswith("/open-apis/bot/v2/hook/"):
        raise OutboundUrlError("飞书 Webhook 地址格式无效")
    return normalized
