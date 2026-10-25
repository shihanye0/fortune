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
from app.models.base import CHINA_TZ
from fortune_engine.bazi.score import get_fortune_level, normalize_score

logger = logging.getLogger(__name__)

# 推送邮件页脚的个人中心入口（生产环境地址，见 CLAUDE.md）
PROFILE_URL = "http://82.157.186.52/profile"

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


def _now_minutes(now: datetime) -> int:
    """当前时刻换算成当天分钟数，用于和时辰区间比较。"""
    return now.hour * 60 + now.minute


def _shichen_bounds(shichen_range: Any) -> tuple[int, int]:
    """时辰区间 "07:00-09:00" 转为 (起始分钟, 结束分钟)；解析失败按全天处理。

    亥时区间为 "22:00-00:00"（跨午夜），结束时间需补一天。
    """
    try:
        start_str, end_str = str(shichen_range).split("-")
        sh, sm = (int(part) for part in start_str.split(":"))
        eh, em = (int(part) for part in end_str.split(":"))
    except (ValueError, AttributeError):
        return 0, 24 * 60
    start = sh * 60 + sm
    end = eh * 60 + em
    if end <= start:
        end += 24 * 60
    return start, end


def _hour_status(item: dict, now_min: int) -> str:
    """时辰相对发送时刻的状态：past（已过）/ current（进行中）/ upcoming（未到）。"""
    start, end = _shichen_bounds(item.get("shichen_range"))
    if now_min >= end:
        return "past"
    if now_min >= start:
        return "current"
    return "upcoming"


def _pick_hourly(hours: list[dict], now_min: int) -> tuple[list[dict], list[dict]]:
    """挑选宜/忌卡片素材：优先尚未结束的时辰；全天已过时退回全量（卡片会带"已过"标记）。

    入选资格按评分取前二，入选后按开始时间排序，阅读顺序即行动顺序。
    """
    if not hours:
        return [], []
    live = [item for item in hours if _hour_status(item, now_min) != "past"]
    pool = live or hours
    ranked = sorted(pool, key=lambda item: normalize_score(item.get("score")), reverse=True)
    by_start = lambda item: _shichen_bounds(item.get("shichen_range"))[0]  # noqa: E731
    favourable = sorted(ranked[:2], key=by_start)
    caution = sorted([item for item in reversed(ranked) if normalize_score(item.get("score")) <= 2][:2], key=by_start)
    return favourable, caution


def _status_badge(status: str, shichen_range: Any) -> str:
    """卡片头部的时辰状态标记：已过 / 进行中 / HH:MM 开始。"""
    if status == "current":
        return (
            '<span style="margin-left:6px; padding:1px 6px; border-radius:999px; '
            'background:#dcfce7; color:#15803d; font-size:10px; font-weight:700;">进行中</span>'
        )
    if status == "past":
        return (
            '<span style="margin-left:6px; padding:1px 6px; border-radius:999px; '
            'background:#f1f5f9; color:#94a3b8; font-size:10px; font-weight:700;">已过</span>'
        )
    start, _ = _shichen_bounds(shichen_range)
    return f'<span style="margin-left:6px; font-size:10px; color:{MUTED};">{start // 60:02d}:{start % 60:02d} 开始</span>'


def _header_meta(fortune_data: dict) -> str:
    """头部日期行：日期 · 干支日 · 冲煞 · 星期，缺失的部分自动跳过。"""
    parts = [_safe(fortune_data.get("date"), "")]
    ganzhi = _safe(fortune_data.get("day_ganzhi"), "")
    if ganzhi:
        parts.append(f"{ganzhi}日")
    chongsha = fortune_data.get("day_chongsha") or {}
    chongsha_short = _safe(chongsha.get("display_short"), "")
    if chongsha_short:
        parts.append(chongsha_short)
    weekday = _weekday_label(fortune_data.get("date"))
    if weekday:
        parts.append(weekday)
    return " · ".join(part for part in parts if part)


HEXAGRAM_TENDENCY_STYLE = {
    "吉": {"label": "吉", "bg": ACT_GOOD},
    "平": {"label": "平", "bg": "#4338ca"},
    "慎": {"label": "慎", "bg": ACT_CAUTION},
}


def _build_hexagram_html(hexagram: dict | None) -> str:
    """今日一卦卡片：六爻时间起卦 + 卦义一句话建议。"""
    if not hexagram or not hexagram.get("name"):
        return ""

    tendency = HEXAGRAM_TENDENCY_STYLE.get(hexagram.get("tendency", "平"), HEXAGRAM_TENDENCY_STYLE["平"])
    changed_name = hexagram.get("changed_name") or ""
    changed_line = f'<span style="margin-left:6px; font-size:11px; color:{MUTED};">变卦 {_safe(changed_name)}</span>' if changed_name else ""
    structure = f"{_safe(hexagram.get('upper_image'))}{_safe(hexagram.get('lower_image'))}"
    return f"""
          <div style="margin-top:20px; padding:14px 16px; background:#f7f9fc; border:1px solid {LINE}; border-left:4px solid #7c3aed; border-radius:10px;">
            <div style="font-size:15px; font-weight:700; color:#1e293b;">☯ 今日一卦</div>
            <div style="margin-top:8px;">
              <span style="display:inline-block; padding:1px 8px; border-radius:999px; background:{tendency['bg']}; color:#ffffff; font-size:11px; font-weight:700;">{tendency['label']}</span>
              <span style="margin-left:6px; font-size:18px; font-weight:700; color:#312e81;">{_safe(hexagram.get("name"))}</span>
              {changed_line}
            </div>
            <div style="margin-top:4px; font-size:11px; color:#94a3b8;">上{_safe(hexagram.get("upper_trigram"))}下{_safe(hexagram.get("lower_trigram"))} · {structure}之象</div>
            <div style="margin-top:6px; font-size:13px; line-height:21px; color:#334155;">{_safe(hexagram.get("advice"))}</div>
          </div>"""


def _preheader(fortune_data: dict, level, score: int, now_min: int) -> str:
    """收件箱列表里显示的预览文案，抓最想被看到的一句。"""
    hours = [item for item in (fortune_data.get("hourly_fortunes") or []) if isinstance(item, dict)]
    hook = ""
    if hours:
        live = [item for item in hours if _hour_status(item, now_min) != "past"] or hours
        best = max(live, key=lambda item: normalize_score(item.get("score")))
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


def _build_season_banner(fortune_data: dict) -> str:
    """节气换月提示横幅：只在换节气当日/前一日出现。"""
    note = fortune_data.get("season_note")
    if not note:
        return ""
    return (
        f'<div style="margin-top:14px; padding:10px 14px; background:#fffbeb; '
        f'border:1px solid #fde68a; border-radius:10px; font-size:13px; color:#92400e;">🍂 {_safe(note)}</div>'
    )


def _build_lucky_html(fortune_data: dict) -> str:
    entries = [
        ("🎨", "幸运色", _safe(fortune_data.get("lucky_color"))),
        ("🔢", "幸运数", _safe(fortune_data.get("lucky_number"))),
        ("🧭", "吉利方位", _safe(fortune_data.get("lucky_direction"))),
    ]
    deity = fortune_data.get("deity_directions") or {}
    if deity.get("caishen"):
        entries.append(("💰", "财神", _safe(deity["caishen"])))
    if deity.get("xishen"):
        entries.append(("😊", "喜神", _safe(deity["xishen"])))
    width = 100 // len(entries) if entries else 100
    cells = "".join(f"""
      <td width="{width}%" align="center" valign="top" style="padding:0 3px;">
        <div style="padding:11px 4px; background:{SURFACE}; border-radius:10px;">
          <div style="font-size:12px; color:{MUTED};">{icon} {label}</div>
          <div style="margin-top:3px; font-size:14px; font-weight:700; color:{BODY};">{value}</div>
        </div>
      </td>""" for icon, label, value in entries)
    return f"""
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:14px;"><tr>{cells}</tr></table>"""


def _build_hourly_strip(hourly_fortunes: list | None, now_min: int) -> str:
    """十二时辰吉时概览条：一屏看清全天起伏，已过时辰置灰、当前时辰高亮。"""
    hours = [item for item in (hourly_fortunes or []) if isinstance(item, dict)]
    if len(hours) < 4:
        return ""

    cells = []
    for item in hours[:12]:
        score = normalize_score(item.get("score"))
        status = _hour_status(item, now_min)
        if status == "past":
            name_color, dot_color, bg = "#cbd5e1", "#e2e8f0", SURFACE
        elif status == "current":
            name_color, dot_color, bg = "#4338ca", get_fortune_level(score).color, "#eef2ff"
        else:
            name_color, dot_color, bg = BODY, get_fortune_level(score).color, SURFACE
        cells.append(f"""
        <td align="center" style="padding:3px;">
          <div style="padding:7px 0 6px; background:{bg}; border-radius:8px;">
            <div style="font-size:13px; font-weight:700; color:{name_color};">{_safe(item.get("shichen"), "")}</div>
            <div style="margin-top:2px; font-size:9px; line-height:10px; color:{dot_color};">●</div>
          </div>
        </td>""")

    row_first = "<tr>" + "".join(cells[:6]) + "</tr>"
    row_second = "<tr>" + "".join(cells[6:12]) + "</tr>"
    return f"""
      <div style="margin-top:10px;">
        <div style="font-size:12px; color:{MUTED};">十二时辰一览 · 灰色为已过，紫色为当前时辰</div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:6px; table-layout:fixed;">{row_first}{row_second}</table>
      </div>"""


def _build_hourly_html(hourly_fortunes: list | None, now_min: int) -> str:
    """只呈现少量可行动的时段，避免在移动端塞入十二行宽表；已过时辰不再作为推荐。"""
    hours = [item for item in (hourly_fortunes or []) if isinstance(item, dict)]
    if not hours:
        return ""

    favourable, caution = _pick_hourly(hours, now_min)

    def card(item: dict, chip: str, accent: str) -> str:
        score = normalize_score(item.get("score"))
        icon = SHICHEN_ICONS.get(item.get("shichen", ""), "⏰")
        status = _hour_status(item, now_min)
        actions = "、".join(item.get("favorable", [])[:2]) or "按自己的节奏安排"
        if chip == "忌":
            actions = "、".join(item.get("unfavorable", [])[:2]) or "重要事项多做一次核对"
        events = "、".join(item.get("events", [])[:2])
        event_line = f"<div style=\"margin-top:4px; color:#64748b;\">{_safe(events)}</div>" if events else ""
        stem = item.get("hourly_stem") or ""
        branch = item.get("hourly_branch") or ""
        ten_god = item.get("ten_god") or ""
        element = item.get("element") or ""
        cause_bits = [f"{stem}{branch}时" if stem and branch else "", ten_god, element]
        cause = " · ".join(bit for bit in cause_bits if bit)
        cause_line = f'<div style="margin-top:3px; font-size:11px; color:#94a3b8;">{_safe(cause)}</div>' if cause else ""
        return f"""
          <div style="margin-top:8px; padding:10px 12px; border-left:3px solid {accent}; background:{SURFACE}; border-radius:0 8px 8px 0;">
            <span style="display:inline-block; padding:1px 8px; border-radius:999px; background:{accent}; color:#ffffff; font-size:11px; font-weight:700;">{chip}</span>
            <span style="font-weight:700; color:#1e293b;"> {icon} {_safe(item.get("shichen"))}时</span>
            <span style="color:{get_fortune_level(score).color}; font-size:12px;"> {score}/5</span>
            {_status_badge(status, item.get("shichen_range"))}
            {cause_line}
            <div style="margin-top:4px; color:#475569;">{_safe(item.get("shichen_range"))} · {_safe(actions)}</div>
            {event_line}
          </div>"""

    cards = "".join(card(item, "宜", ACT_GOOD) for item in favourable)
    cards += "".join(card(item, "忌", ACT_CAUTION) for item in caution)
    strip = _build_hourly_strip(hours, now_min)
    return f"""
      <div style="margin-top:22px;">
        <div style="font-size:15px; font-weight:700; color:#1e293b;">今日行动节奏</div>
        <div style="margin-top:3px; font-size:12px; color:{MUTED};">优先推荐尚未开始的时段，仅供日程安排参考。</div>
        {strip}
        {cards}
      </div>"""


def _event_time_label(event: dict, now_min: int) -> str:
    """事件最佳时段标签：辰时 07:00-09:00 / 辰时 / 全天；已过的时段直接标注。"""
    best_hour = event.get("best_hour") or ""
    time_range = event.get("time_range") or ""
    if time_range and time_range != "全天":
        if _hour_status({"shichen_range": time_range}, now_min) == "past":
            return "已过"
        return f"{best_hour}时 {time_range}" if best_hour else time_range
    return f"{best_hour}时" if best_hour else "全天"


def _build_events_html(events: list | None, now_min: int) -> str:
    if not events:
        return ""

    rows = []
    for event in events[:3]:
        time_label = _event_time_label(event, now_min)
        time_color = "#94a3b8" if time_label == "已过" else MUTED
        rows.append(f"""
          <tr>
            <td width="72" style="padding:8px 0; border-bottom:1px solid {LINE};">
              <span style="display:inline-block; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#4338ca; font-size:11px; font-weight:600;">{_safe(event.get("dimension"))}</span>
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid {LINE}; color:{BODY};">{_safe(event.get("event"))}</td>
            <td width="104" align="right" valign="top" style="padding:8px 0; border-bottom:1px solid {LINE};">
              <span style="font-size:11px; line-height:16px; color:{time_color}; white-space:nowrap;">{_safe(time_label)}</span>
            </td>
          </tr>""")

    return f"""
      <div style="margin-top:22px;">
        <div style="font-size:15px; font-weight:700; color:#1e293b;">今日行动关注点</div>
        <div style="margin-top:3px; font-size:12px; color:{MUTED};">按当日节奏生成，右侧为建议时段，适合用作安排优先级的参考。</div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:7px; font-size:13px;">
          {''.join(rows)}
        </table>
      </div>"""


def _build_recap_html(recap: dict | None) -> str:
    """本周回顾板块（周日）：周均分 + 预言命中率，突出反馈闭环。"""
    if not recap:
        return ""
    rows = []
    if recap.get("week_avg_score") is not None:
        rows.append(
            f'<div style="font-size:13px; color:{BODY};">📈 本周均分 '
            f'<b>{recap["week_avg_score"]}/5</b>（共 {recap.get("days_count", 0)} 天）</div>'
        )
    if recap.get("verified_total"):
        rows.append(
            f'<div style="margin-top:4px; font-size:13px; color:{BODY};">🎯 预言命中 '
            f'<b>{recap["hit_count"]}/{recap["verified_total"]}</b>（{recap["hit_rate"]}%）'
            f'<span style="font-size:11px; color:{MUTED};"> · 数据来自你的真实反馈</span></div>'
        )
    else:
        rows.append(
            f'<div style="margin-top:4px; font-size:13px; color:{MUTED};">还没有预言反馈——'
            f'<a href="{PROFILE_URL}" style="color:#6366f1;">去给预测打个分</a>，看看准不准</div>'
        )
    return f"""
      <div style="margin-top:22px; padding:14px 16px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px;">
        <div style="font-size:15px; font-weight:700; color:#14532d;">📊 本周回顾</div>
        {''.join(rows)}
      </div>"""


def _build_html(fortune_data: dict, now: datetime | None = None) -> str:
    """构建兼容主流邮箱、优先移动端阅读的日运简报。"""
    now = now or datetime.now(CHINA_TZ)
    now_min = _now_minutes(now)
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

    reflection_html = ""
    question = fortune_data.get("reflection_question")
    if question:
        reflection_html = (
            f'<div style="margin-top:10px; padding-top:10px; border-top:1px dashed #ddd6fe; '
            f'font-size:13px; color:#4338ca;">💭 今日一问：{_safe(question)}</div>'
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;">
  <span style="display:none; max-height:0; overflow:hidden; mso-hide:all; font-size:1px; line-height:1px; color:#f1f5f9;">{_preheader(fortune_data, level, score, now_min)}</span>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="620" cellspacing="0" cellpadding="0" style="width:100%; max-width:620px; background:#ffffff; border-radius:16px; overflow:hidden;">
        <tr><td style="padding:26px 28px; background-color:{INK}; background-image:linear-gradient(135deg,#172554 0%,#4c1d95 100%); color:#ffffff;">
          <div style="font-size:11px; letter-spacing:2px; color:#c7d2fe;">DAILY FORTUNE BRIEF</div>
          <div style="margin-top:8px; font-size:25px; font-weight:700;">今日运势简报</div>
          <div style="margin-top:6px; font-size:13px; color:#e0e7ff;">{_header_meta(fortune_data)}</div>
        </td></tr>
        <tr><td style="padding:0 28px 28px;">
          {_build_season_banner(fortune_data)}
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
            {reflection_html}
          </div>
          {_build_hexagram_html(fortune_data.get("daily_hexagram"))}
          {_build_hourly_html(fortune_data.get("hourly_fortunes"), now_min)}
          {_build_events_html(fortune_data.get("probability_events"), now_min)}
          {_build_recap_html(fortune_data.get("weekly_recap"))}
          <div style="margin-top:24px; padding-top:14px; border-top:1px solid {LINE}; font-size:11px; line-height:17px; color:#94a3b8;">
            本内容以传统文化信息为参考，不构成医疗、法律、投资或其他重要决策建议。<br>
            推送时间与渠道可在<a href="{PROFILE_URL}" style="color:#6366f1; text-decoration:underline;">个人中心</a>调整。<br>
            本邮件由命理运势系统自动发送。
          </div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_text(fortune_data: dict, now: datetime | None = None) -> str:
    """为纯文本客户端、屏幕阅读器保留同等信息。"""
    now = now or datetime.now(CHINA_TZ)
    now_min = _now_minutes(now)
    score = normalize_score(fortune_data.get("overall_score"))
    level = get_fortune_level(score)
    lines = [
        "每日运势简报",
        str(fortune_data.get("date") or ""),
    ]
    ganzhi = fortune_data.get("day_ganzhi")
    if ganzhi:
        lines.append(f"干支：{ganzhi}日")
    chongsha = fortune_data.get("day_chongsha") or {}
    if chongsha.get("display"):
        lines.append(f"冲煞：{chongsha['display']}")
    season_note = fortune_data.get("season_note")
    if season_note:
        lines.append(f"节气：{season_note}")
    lines.extend([
        f"综合状态：{score}/5 · {level.label}",
        level.guidance,
        "",
    ])
    for label, key in (("事业", "career"), ("财运", "wealth"), ("感情", "love"), ("健康", "health")):
        dimension = fortune_data.get(key) or {}
        detail = dimension.get("detail") or dimension.get("description") or "—"
        lines.append(f"{label}：{normalize_score(dimension.get('score'))}/5 · {detail}")
    deity = fortune_data.get("deity_directions") or {}
    lines.extend([
        "",
        f"幸运色：{fortune_data.get('lucky_color') or '—'}",
        f"幸运数：{fortune_data.get('lucky_number') or '—'}",
        f"吉利方位：{fortune_data.get('lucky_direction') or '—'}",
    ])
    if deity.get("caishen"):
        lines.append(f"财神方位：{deity['caishen']}")
    if deity.get("xishen"):
        lines.append(f"喜神方位：{deity['xishen']}")
    hours = [item for item in (fortune_data.get("hourly_fortunes") or []) if isinstance(item, dict)]
    favourable, caution = _pick_hourly(hours, now_min)
    if favourable:
        summary = "、".join(
            f"{item.get('shichen', '')}时 {item.get('shichen_range') or ''}（{normalize_score(item.get('score'))}/5）"
            for item in favourable
        )
        lines.append(f"今日吉时：{summary}")
    if caution:
        summary = "、".join(
            f"{item.get('shichen', '')}时 {item.get('shichen_range') or ''}（{normalize_score(item.get('score'))}/5）"
            for item in caution
        )
        lines.append(f"需留意时辰：{summary}")
    hexagram = fortune_data.get("daily_hexagram") or {}
    if hexagram.get("name"):
        line = f"今日一卦：{hexagram['name']}（{hexagram.get('tendency', '平')}）——{hexagram.get('advice', '')}"
        if hexagram.get("changed_name"):
            line += f"；变卦 {hexagram['changed_name']}"
        lines.append(line)
    events = fortune_data.get("probability_events") or []
    if events:
        parts = []
        for event in events[:3]:
            label = _event_time_label(event, now_min)
            suffix = f"（建议时段：{label}）" if label != "全天" else ""
            parts.append(f"{event.get('event', '')}{suffix}")
        lines.extend(["", "今日行动关注点："] + [f"- {part}" for part in parts])
    if fortune_data.get("interpretation"):
        lines.extend(["", "运势解读：", str(fortune_data["interpretation"])])
    question = fortune_data.get("reflection_question")
    if question:
        lines.append(f"今日一问：{question}")
    recap = fortune_data.get("weekly_recap") or {}
    if recap:
        parts = []
        if recap.get("week_avg_score") is not None:
            parts.append(f"本周均分 {recap['week_avg_score']}/5（{recap.get('days_count', 0)} 天）")
        if recap.get("verified_total"):
            parts.append(f"预言命中 {recap['hit_count']}/{recap['verified_total']}（{recap['hit_rate']}%）")
        if parts:
            lines.extend(["", "本周回顾：" + "；".join(parts)])
    lines.extend(["", f"推送设置：{PROFILE_URL}", "传统文化参考，不构成重要决策建议。"])
    return "\n".join(lines)


def send_fortune_email(to_email: str, fortune_data: dict) -> bool:
    """发送带纯文本降级内容的日运简报邮件。"""
    date_str = fortune_data.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        subject = f"【命理运势·日运简报】{dt.year}年{dt.month}月{dt.day}日"
    except (ValueError, TypeError):
        subject = f"【命理运势·日运简报】{date_str}"

    now = datetime.now(CHINA_TZ)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(_build_text(fortune_data, now), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(fortune_data, now), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("邮件发送成功: %s", to_email)
        return True
    except Exception as exc:
        logger.error("邮件发送失败: %s -> %s", to_email, type(exc).__name__)
        return False
