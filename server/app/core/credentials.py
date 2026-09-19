"""用户自带 API Key 的加密存储。"""
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)

_PREFIX = "fernet:v1:"


class CredentialError(ValueError):
    """密钥加密配置缺失或密文无效。"""


def _cipher() -> Fernet:
    key = settings.LLM_CREDENTIAL_ENCRYPTION_KEY.strip()
    if not key:
        raise CredentialError("服务端尚未配置个人 API Key 加密密钥")
    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CredentialError("个人 API Key 加密密钥格式无效") from exc


def encrypt_user_api_key(value: str) -> str:
    """返回可识别版本的 Fernet 密文，不记录原始 Key。"""
    return _PREFIX + _cipher().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_user_api_key(value: str | None) -> str | None:
    """读取新密文；历史明文只做临时兼容并发出迁移告警。"""
    if not value:
        return None
    if not value.startswith(_PREFIX):
        logger.warning("检测到待迁移的个人 LLM API Key 明文，建议用户重新保存配置")
        return value
    try:
        return _cipher().decrypt(value[len(_PREFIX):].encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, CredentialError) as exc:
        raise CredentialError("无法解密已保存的个人 API Key") from exc
