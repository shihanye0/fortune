# -*- coding: utf-8 -*-
"""QQ 邮箱日运简报推送服务。"""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Any

from app.config import settings
from fortune_engine.bazi.score import get_fortune_level, normalize_score

logger = logging.getLogger(__name__)

SHICHEN_ICONS = {
    "子": "🌙", "丑": "🌑", "寅": "🌅", "卯": "🌄",
    "辰": "☀️", "巳": "🌞", "午": "⛅", "未": "🌤️",
    "申": "🌇", "酉": "🌆", "戌": "🌃", "亥": "🌌",
}

WEEKDAY_NAMES = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

# 常用配色：邮箱客户端样式支持差异大，全部使用内联样式与纯色回退。
INK = "#1e1b4b"
BODY = "#334155"
MUTED = "#64748b"
LINE = "#e2e8f0"
SURFACE = "#f8fafc"

ACT_GOOD = "#0f766e"
ACT_CAUTION = "#b45309"


def _safe(value: Any, default: str = "—") -> str:
    """转义所有可能来自用户、LLM 或数据库的 HTML 内容。"""
    if value is None or value == "":
        return default
    return escape(str(value), quote=True)


def _safe_paragraph(value: Any) -> str:
    return _safe(value).replace("\n", "<br>")


def _dimension_detail(dimension: dict | None) -> str:
    dimension = dimension or {}
    return _safe(dimension.get("detail") or dimension.get("description"))


def _dot_meter(score: int, color: str) -> str:
    """五段圆点量表：所有客户端可渲染的"进度条"。"""
    score = max(0, min(5, score))
    filled = "●" * score
    empty = "○" * (5 - score)
    return (
        f'<span style="color:{color}; font-size:11px; letter-spacing:2px;">{filled}</span>'
        f'<span style="color:#cbd5e1; font-size:11px; letter-spacing:2px;">{empty}</span>'
    )


def _weekday_label(date_value: Any) -> str:
    try:
        dt = datetime.strptime(str(date_value), "%Y-%m-%d")
    except (ValueError, TypeError):
        return ""
    return WEEKDAY_NAMES[dt.weekday()]


def _header_meta(fortune_data: dict) -> str:
    """头部日期行：日期 · 干支日 · 星期，缺失的部分自动跳过。"""
    parts = [_safe(fortune_data.get("date"), "")]
    ganzhi = _safe(fortune_data.get("day_ganzhi"), "")
    if ganzhi:
        parts.append(f"{ganzhi}日")
    weekday = _weekday_label(fortune_data.get("date"))
    if weekday:
        parts.append(weekday)
    return " · ".join(part for part in parts if part)


def _preheader(fortune_data: dict, level, score: int) -> str:
    """收件箱列表里显示的预览文案，抓最想被看到的一句。"""
    hours = [item for item in (fortune_data.get("hourly_fortunes") or []) if isinstance(item, dict)]
    hook = ""
    if hours:
        best = max(hours, key=lambda item: normalize_score(item.get("score")))
        actions = "、".join(best.get("favorable", [])[:2])
        if actions:
            hook = f"{_safe(best.get('shichen'), '')}时宜{actions}。"
    text = f"综合{score}/5 · {level.label}。{hook}{level.guidance}"
    return escape(text[:60], quote=True)


def _dimension_cell(label: str, icon: str, dimension: dict | None, tint: str) -> str:
    dimension = dimension or {}
    score = normalize_score(dimension.get("score"))
    level = get_fortune_level(score)
    return f"""
      <td width="50%" valign="top" style="padding:5px;">
        <div style="min-height:112px; box-sizing:border-box; padding:13px 14px; background:{tint}; border-radius:12px;">
          <div style="font-size:13px; color:#475569;">{icon} {label}</div>
          <div style="margin-top:4px;">
            <span style="font-size:21px; font-weight:700; color:{level.color};">{score}</span><span style="font-size:12px; color:{MUTED};"> / 5</span>
            <span style="margin-left:6px;">{_dot_meter(score, level.color)}</span>
          </div>
          <div style="margin-top:5px; font-size:12px; line-height:18px; color:#64748b;">{_dimension_detail(dimension)}</div>
        </div>
      </td>"""


def _build_lucky_html(fortune_data: dict) -> str:
    cells = []
    for icon, label, key in (
        ("🎨", "幸运色", "lucky_color"),
        ("🔢", "幸运数", "lucky_number"),
        ("🧭", "吉利方位", "lucky_direction"),
    ):
        cells.append(f"""
      <td width="33%" align="center" valign="top" style="padding:0 3px;">
        <div style="padding:11px 4px; background:{SURFACE}; border-radius:10px;">
          <div style="font-size:12px; color:{MUTED};">{icon} {label}</div>
          <div style="margin-top:3px; font-size:14px; font-weight:700; color:{BODY};">{_safe(fortune_data.get(key))}</div>
        </div>
      </td>""")
    return f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:14px;"><tr>{''.join(cells)}</tr></table>"""


def _build_hourly_strip(hourly_fortunes: list | None) -> str:
    """十二时辰吉时概览条：一屏看清全天起伏，细节交给下面的重点卡片。"""
    hours = [item for item in (hourly_fortunes or []) if isinstance(item, dict)]
    if len(hours) < 4:
        return ""

    cells = []
    for item in hours[:12]:
        score = normalize_score(item.get("score"))
        color = get_fortune_level(score).color
        cells.append(f"""
        <td align="center" style="padding:3px;">
          <div style="padding:7px 0 6px; background:{SURFACE}; border-radius:8px;">
            <div style="font-size:13px; font-weight:700; color:{BODY};">{_safe(item.get("shichen"), "")}</div>
            <div style="margin-top:2px; font-size:9px; line-height:10px; color:{color};">●</div>
          </div>
        </td>""")

    row_first = "<tr>" + "".join(cells[:6]) + "</tr>"
    row_second = "<tr>" + "".join(cells[6:12]) + "</tr>"
    return f"""
      <div style="margin-top:10px;">
        <div style="font-size:12px; color:{MUTED};">十二时辰一览 · 圆点颜色对应各时辰评分</div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:6px; table-layout:fixed;">{row_first}{row_second}</table>
      </div>"""


def _build_hourly_html(hourly_fortunes: list | None) -> str:
    """只呈现少量可行动的时段，避免在移动端塞入十二行宽表。"""
    hours = [item for item in (hourly_fortunes or []) if isinstance(item, dict)]
    if not hours:
        return ""

    ranked = sorted(hours, key=lambda item: normalize_score(item.get("score")))
    favourable = list(reversed(ranked))[:2]
    caution = [item for item in ranked if normalize_score(item.get("score")) <= 2][:2]

    def card(item: dict, chip: str, accent: str) -> str:
        score = normalize_score(item.get("score"))
        icon = SHICHEN_ICONS.get(item.get("shichen", ""), "⏰")
        actions = "、".join(item.get("favorable", [])[:2]) or "按自己的节奏安排"
        if chip == "忌":
            actions = "、".join(item.get("unfavorable", [])[:2]) or "重要事项多做一次核对"
        events = "、".join(item.get("events", [])[:2])
        event_line = f"<div style=\"margin-top:4px; color:#64748b;\">{_safe(events)}</div>" if events else ""
        return f"""
          <div style="margin-top:8px; padding:10px 12px; border-left:3px solid {accent}; background:{SURFACE}; border-radius:0 8px 8px 0;">
            <span style="display:inline-block; padding:1px 8px; border-radius:999px; background:{accent}; color:#ffffff; font-size:11px; font-weight:700;">{chip}</span>
            <span style="font-weight:700; color:#1e293b;"> {icon} {_safe(item.get("shichen"))}时</span>
            <span style="color:{get_fortune_level(score).color}; font-size:12px;"> {score}/5</span>
            <div style="margin-top:4px; color:#475569;">{_safe(item.get("shichen_range"))} · {_safe(actions)}</div>
            {event_line}
          </div>"""

    cards = "".join(card(item, "宜", ACT_GOOD) for item in favourable)
    cards += "".join(card(item, "忌", ACT_CAUTION) for item in caution)
    strip = _build_hourly_strip(hours)
    return f"""
      <div style="margin-top:22px;">
        <div style="font-size:15px; font-weight:700; color:#1e293b;">今日行动节奏</div>
        <div style="margin-top:3px; font-size:12px; color:{MUTED};">从时辰数据中挑出的重点时段，仅供日程安排参考。</div>
        {strip}
        {cards}
      </div>"""


def _build_events_html(events: list | None) -> str:
    if not events:
        return ""

    rows = []
    for event in events[:3]:
        rows.append(f"""
          <tr>
            <td width="72" style="padding:8px 0; border-bottom:1px solid {LINE};">
              <span style="display:inline-block; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#4338ca; font-size:11px; font-weight:600;">{_safe(event.get("dimension"))}</span>
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid {LINE}; color:{BODY};">{_safe(event.get("event"))}</td>
          </tr>""")

    return f"""
      <div style="margin-top:22px;">
        <div style="font-size:15px; font-weight:700; color:#1e293b;">今日行动关注点</div>
        <div style="margin-top:3px; font-size:12px; color:{MUTED};">按当日节奏生成，适合用作安排优先级的参考。</div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:7px; font-size:13px;">
          {''.join(rows)}
        </table>
      </div>"""


def _build_html(fortune_data: dict) -> str:
    """构建兼容主流邮箱、优先移动端阅读的日运简报。"""
    score = normalize_score(fortune_data.get("overall_score"))
    level = get_fortune_level(score)
    career = fortune_data.get("career") or {}
    wealth = fortune_data.get("wealth") or {}
    love = fortune_data.get("love") or {}
    health = fortune_data.get("health") or {}

    dimensions = f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:14px;">
        <tr>
          {_dimension_cell("事业", "💼", career, "#f0fdfa")}
          {_dimension_cell("财运", "💰", wealth, "#fffbeb")}
        </tr>
        <tr>
          {_dimension_cell("感情", "💕", love, "#fdf2f8")}
          {_dimension_cell("健康", "🏥", health, "#eff6ff")}
        </tr>
      </table>"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;">
  <span style="display:none; max-height:0; overflow:hidden; mso-hide:all; font-size:1px; line-height:1px; color:#f1f5f9;">{_preheader(fortune_data, level, score)}</span>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="620" cellspacing="0" cellpadding="0" style="width:100%; max-width:620px; background:#ffffff; border-radius:16px; overflow:hidden;">
        <tr><td style="padding:26px 28px; background-color:{INK}; background-image:linear-gradient(135deg,#172554 0%,#4c1d95 100%); color:#ffffff;">
          <div style="font-size:11px; letter-spacing:2px; color:#c7d2fe;">DAILY FORTUNE BRIEF</div>
          <div style="margin-top:8px; font-size:25px; font-weight:700;">今日运势简报</div>
          <div style="margin-top:6px; font-size:13px; color:#e0e7ff;">{_header_meta(fortune_data)}</div>
        </td></tr>
        <tr><td style="padding:0 28px 28px;">
          <div style="margin-top:16px; padding:18px 20px; background:{SURFACE}; border:1px solid {LINE}; border-radius:14px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>
              <td valign="middle">
                <div style="font-size:12px; color:{MUTED}; letter-spacing:1px;">综合状态</div>
                <div style="margin-top:4px; font-size:24px; font-weight:700; color:{level.color};">{level.label}</div>
                <div style="margin-top:6px;">{_dot_meter(score, level.color)}</div>
                <div style="margin-top:6px; font-size:12px; line-height:18px; color:{MUTED};">{level.guidance}</div>
              </td>
              <td width="86" align="right" valign="middle">
                <div style="width:76px; height:76px; line-height:76px; text-align:center; border-radius:50%; background:{level.color}; color:#ffffff; font-size:28px; font-weight:700;">
                  {score}<span style="font-size:13px;">/5</span>
                </div>
              </td>
            </tr></table>
          </div>
          {dimensions}
          {_build_lucky_html(fortune_data)}
          <div style="margin-top:20px; padding:14px 16px; background:#fafaff; border:1px solid #ddd6fe; border-left:4px solid #6366f1; border-radius:10px;">
            <div style="font-size:15px; font-weight:700; color:#312e81;">运势解读</div>
            <div style="margin-top:8px; font-size:14px; line-height:24px; color:#334155;">{_safe_paragraph(fortune_data.get("interpretation"))}</div>
          </div>
          {_build_hourly_html(fortune_data.get("hourly_fortunes"))}
          {_build_events_html(fortune_data.get("probability_events"))}
          <div style="margin-top:24px; padding-top:14px; border-top:1px solid {LINE}; font-size:11px; line-height:17px; color:#94a3b8;">
            本内容以传统文化信息为参考，不构成医疗、法律、投资或其他重要决策建议。<br>
            本邮件由命理运势系统自动发送。
          </div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_text(fortune_data: dict) -> str:
    """为纯文本客户端、屏幕阅读器保留同等信息。"""
    score = normalize_score(fortune_data.get("overall_score"))
    level = get_fortune_level(score)
    lines = [
        "每日运势简报",
        str(fortune_data.get("date") or ""),
    ]
    ganzhi = fortune_data.get("day_ganzhi")
    if ganzhi:
        lines.append(f"干支：{ganzhi}日")
    lines.extend([
        f"综合状态：{score}/5 · {level.label}",
        level.guidance,
        "",
    ])
    for label, key in (("事业", "career"), ("财运", "wealth"), ("感情", "love"), ("健康", "health")):
        dimension = fortune_data.get(key) or {}
        detail = dimension.get("detail") or dimension.get("description") or "—"
        lines.append(f"{label}：{normalize_score(dimension.get('score'))}/5 · {detail}")
    lines.extend([
        "",
        f"幸运色：{fortune_data.get('lucky_color') or '—'}",
        f"幸运数：{fortune_data.get('lucky_number') or '—'}",
        f"吉利方位：{fortune_data.get('lucky_direction') or '—'}",
    ])
    if fortune_data.get("interpretation"):
        lines.extend(["", "运势解读：", str(fortune_data["interpretation"])])
    lines.extend(["", "传统文化参考，不构成重要决策建议。"])
    return "\n".join(lines)


def send_fortune_email(to_email: str, fortune_data: dict) -> bool:
    """发送带纯文本降级内容的日运简报邮件。"""
    date_str = fortune_data.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        subject = f"【命理运势·日运简报】{dt.year}年{dt.month}月{dt.day}日"
    except (ValueError, TypeError):
        subject = f"【命理运势·日运简报】{date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(_build_text(fortune_data), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(fortune_data), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("邮件发送成功: %s", to_email)
        return True
    except Exception as exc:
        logger.error("邮件发送失败: %s -> %s", to_email, type(exc).__name__)
        return False
