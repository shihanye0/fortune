# -*- coding: utf-8 -*-
"""Spec 016: QQ 邮箱推送服务（增强版）"""
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)

# 时辰图标
SHICHEN_ICONS = {
    '子': '🌙', '丑': '🌑', '寅': '🌅', '卯': '🌄',
    '辰': '☀️', '巳': '🌞', '午': '⛅', '未': '🌤️',
    '申': '🌇', '酉': '🌆', '戌': '🌃', '亥': '🌌',
}


def _score_color(score: int) -> str:
    if score >= 4:
        return '#22c55e'
    if score >= 3:
        return '#eab308'
    return '#ef4444'


def _build_hourly_html(hourly_fortunes: list) -> str:
    """构建时辰运势 HTML"""
    if not hourly_fortunes:
        return ''

    rows = ''
    for h in hourly_fortunes:
        icon = SHICHEN_ICONS.get(h.get('shichen', ''), '⏰')
        color = _score_color(h.get('score', 3))
        favorable = '、'.join(h.get('favorable', []))
        unfavorable = '、'.join(h.get('unfavorable', []))
        events = '、'.join(h.get('events', []))

        rows += f'''
        <tr>
          <td style="padding:8px; text-align:center; border-bottom:1px solid #f0f0f0;">
            {icon} {h.get('shichen', '')}时<br>
            <span style="font-size:11px; color:#999;">{h.get('shichen_range', '')}</span>
          </td>
          <td style="padding:8px; text-align:center; border-bottom:1px solid #f0f0f0;">
            <span style="color:{color}; font-weight:bold; font-size:18px;">{h.get('score', '-')}</span>
          </td>
          <td style="padding:8px; border-bottom:1px solid #f0f0f0; font-size:12px; color:#666;">
            {events}
          </td>
          <td style="padding:8px; border-bottom:1px solid #f0f0f0; font-size:12px;">
            <span style="color:#22c55e;">宜：{favorable}</span><br>
            <span style="color:#ef4444;">忌：{unfavorable}</span>
          </td>
        </tr>'''

    return f'''
    <div style="margin-top:20px;">
      <h3 style="color:#d4380d; margin-bottom:10px;">⏰ 时辰运势</h3>
      <table style="width:100%; border-collapse:collapse; font-size:13px;">
        <tr style="background:#fafafa;">
          <th style="padding:8px; text-align:center;">时辰</th>
          <th style="padding:8px; text-align:center;">评分</th>
          <th style="padding:8px; text-align:center;">事件</th>
          <th style="padding:8px; text-align:center;">宜忌</th>
        </tr>
        {rows}
      </table>
    </div>'''


def _build_events_html(events: list) -> str:
    """构建概率事件 HTML"""
    if not events:
        return ''

    rows = ''
    for e in events:
        prob = e.get('probability', 0)
        if prob >= 70:
            color = '#22c55e'
            label = '高'
        elif prob >= 40:
            color = '#eab308'
            label = '中'
        else:
            color = '#ef4444'
            label = '低'

        rows += f'''
        <div style="display:inline-block; margin:4px; padding:8px 12px; background:#fff; border-radius:8px; border:1px solid #f0f0f0;">
          <span style="font-size:12px; color:#666;">{e.get('dimension', '')}</span><br>
          <span style="font-weight:bold; color:#333;">{e.get('event', '')}</span><br>
          <span style="color:{color}; font-weight:bold;">{prob}%</span>
          <span style="font-size:11px; color:#999;">（{label}概率）</span>
        </div>'''

    return f'''
    <div style="margin-top:20px;">
      <h3 style="color:#d4380d; margin-bottom:10px;">🎲 今日概率事件</h3>
      <div style="padding:10px; background:#fafafa; border-radius:8px;">
        {rows}
      </div>
    </div>'''


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
    hourly_fortunes = fortune_data.get("hourly_fortunes", [])
    probability_events = fortune_data.get("probability_events", [])

    # 运势等级
    if score >= 90:
        score_text = "大吉"
    elif score >= 70:
        score_text = "中吉"
    elif score >= 50:
        score_text = "小吉"
    else:
        score_text = "平"

    hourly_html = _build_hourly_html(hourly_fortunes)
    events_html = _build_events_html(probability_events)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Microsoft YaHei', sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
  <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

    <!-- 标题 -->
    <h1 style="text-align: center; color: #d4380d; margin-bottom: 5px;">每日运势播报</h1>
    <p style="text-align: center; color: #999; font-size: 14px;">{date_str}</p>

    <!-- 综合评分 -->
    <div style="text-align: center; margin: 20px 0;">
      <div style="display:inline-block; width:100px; height:100px; border-radius:50%; background:linear-gradient(135deg, #d4380d, #ff7a45); line-height:100px;">
        <span style="font-size: 42px; color: #fff; font-weight: bold;">{score}</span>
      </div>
      <div style="margin-top:8px; font-size:16px; color:#d4380d; font-weight:bold;">{score_text}</div>
    </div>

    <!-- 四维评分 -->
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr>
        <td style="padding: 12px; text-align: center; background: #fff7e6; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">💼 事业运</div>
          <div style="font-size: 28px; color: #d4380d; font-weight: bold;">{career.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{career.get('description', '')}</div>
        </td>
        <td style="padding: 12px; text-align: center; background: #f6ffed; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">💰 财运</div>
          <div style="font-size: 28px; color: #389e0d; font-weight: bold;">{wealth.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{wealth.get('description', '')}</div>
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; text-align: center; background: #fff0f6; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">💕 感情运</div>
          <div style="font-size: 28px; color: #eb2f96; font-weight: bold;">{love.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{love.get('description', '')}</div>
        </td>
        <td style="padding: 12px; text-align: center; background: #e6f7ff; border-radius: 8px;">
          <div style="font-size: 14px; color: #999;">🏥 健康运</div>
          <div style="font-size: 28px; color: #1890ff; font-weight: bold;">{health.get('score', '-')}</div>
          <div style="font-size: 12px; color: #666;">{health.get('description', '')}</div>
        </td>
      </tr>
    </table>

    <!-- 幸运信息 -->
    <div style="background: #fafafa; padding: 15px; border-radius: 8px; margin: 15px 0;">
      <span style="margin-right:20px;">🎨 <b>幸运色：</b>{lucky_color}</span>
      <span style="margin-right:20px;">🔢 <b>幸运数：</b>{lucky_number}</span>
      <span>🧭 <b>吉方位：</b>{lucky_direction}</span>
    </div>

    <!-- 运势解读 -->
    <div style="margin-top: 20px; padding: 20px; background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(245,158,11,0.08)); border-radius: 8px; border: 1px solid rgba(99,102,241,0.15);">
      <h3 style="color: #6366f1; margin-top: 0;">🔮 运势解读</h3>
      <p style="color: #333; line-height: 1.8; margin: 0;">{interpretation}</p>
    </div>

    <!-- 时辰运势 -->
    {hourly_html}

    <!-- 概率事件 -->
    {events_html}

    <!-- 底部 -->
    <p style="text-align: center; color: #ccc; font-size: 12px; margin-top: 30px;">
      命理运势系统 · 仅供参考 · 祝您今日顺利
    </p>
  </div>
</body>
</html>"""


def send_fortune_email(to_email: str, fortune_data: dict) -> bool:
    """发送运势邮件"""
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
