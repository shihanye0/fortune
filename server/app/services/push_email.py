# -*- coding: utf-8 -*-
"""Spec 016: QQ 邮箱推送服务"""
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_html(fortune_data: dict) -> str:
    """构建运势邮件 HTML"""
    date_str = fortune_data.get("date", "")
    score = fortune_data.get("overall_score", 0)
    career = fortune_data.get("career", {})
    wealth = fortune_data.get("wealth", {})
    love = fortune_data.get("love", {})
    health = fortune_data.get("health", {})
    lucky_color = fortune_data.get("lucky_color", "-")
    lucky_number = fortune_data.get("lucky_number", "-")
    lucky_direction = fortune_data.get("lucky_direction", "-")
    interpretation = fortune_data.get("interpretation", "")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
  <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h1 style="text-align: center; color: #d4380d; margin-bottom: 5px;">每日运势播报</h1>
    <p style="text-align: center; color: #999; font-size: 14px;">{date_str}</p>

    <div style="text-align: center; margin: 20px 0;">
      <span style="font-size: 48px; color: #d4380d; font-weight: bold;">{score}</span>
      <span style="font-size: 16px; color: #999;">/100</span>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr>
        <td style="padding: 10px; text-align: center; background: #fff7e6; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">事业运</div>
          <div style="font-size: 24px; color: #d4380d; font-weight: bold;">{career.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{career.get('detail', '')}</div>
        </td>
        <td style="padding: 10px; text-align: center; background: #f6ffed; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">财运</div>
          <div style="font-size: 24px; color: #389e0d; font-weight: bold;">{wealth.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{wealth.get('detail', '')}</div>
        </td>
      </tr>
      <tr>
        <td style="padding: 10px; text-align: center; background: #fff0f6; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">感情运</div>
          <div style="font-size: 24px; color: #eb2f96; font-weight: bold;">{love.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{love.get('detail', '')}</div>
        </td>
        <td style="padding: 10px; text-align: center; background: #e6f7ff; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">健康运</div>
          <div style="font-size: 24px; color: #1890ff; font-weight: bold;">{health.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{health.get('detail', '')}</div>
        </td>
      </tr>
    </table>

    <div style="background: #fafafa; padding: 15px; border-radius: 8px; margin: 15px 0;">
      <p style="margin: 5px 0;"><b>幸运色：</b>{lucky_color}</p>
      <p style="margin: 5px 0;"><b>幸运数：</b>{lucky_number}</p>
      <p style="margin: 5px 0;"><b>吉方位：</b>{lucky_direction}</p>
    </div>

    <div style="margin-top: 20px; padding: 15px; background: #fffbe6; border-radius: 8px;">
      <h3 style="color: #d4380d; margin-top: 0;">大师解读</h3>
      <p style="color: #333; line-height: 1.8;">{interpretation}</p>
    </div>

    <p style="text-align: center; color: #ccc; font-size: 12px; margin-top: 30px;">
      命理运势系统 · 仅供参考
    </p>
  </div>
</body>
</html>"""


def send_fortune_email(to_email: str, fortune_data: dict) -> bool:
    """发送运势邮件

    Args:
        to_email: 收件人邮箱
        fortune_data: 运势数据字典

    Returns:
        True 发送成功, False 发送失败
    """
    date_str = fortune_data.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        subject = f"【命理运势】{dt.year}年{dt.month}月{dt.day}日 运势播报"
    except (ValueError, TypeError):
        subject = f"【命理运势】{date_str} 运势播报"

    html_body = _build_html(fortune_data)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("邮件发送成功: %s", to_email)
        return True
    except Exception as e:
        logger.error("邮件发送失败: %s -> %s", to_email, e)
        return False
