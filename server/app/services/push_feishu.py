# -*- coding: utf-8 -*-
"""Spec 017: 飞书机器人推送服务（增强版）"""
import logging

import httpx

logger = logging.getLogger(__name__)


def _build_hourly_text(hourly_fortunes: list) -> str:
    """构建时辰运势文本"""
    if not hourly_fortunes:
        return ''

    icons = {
        '子': '🌙', '丑': '🌑', '寅': '🌅', '卯': '🌄',
        '辰': '☀️', '巳': '🌞', '午': '⛅', '未': '🌤️',
        '申': '🌇', '酉': '🌆', '戌': '🌃', '亥': '🌌',
    }

    lines = ['**⏰ 时辰运势**\n']
    for h in hourly_fortunes:
        icon = icons.get(h.get('shichen', ''), '⏰')
        score = h.get('score', 3)
        if score >= 4:
            score_tag = f"<font color='green'>{score}分</font>"
        elif score >= 3:
            score_tag = f"<font color='orange'>{score}分</font>"
        else:
            score_tag = f"<font color='red'>{score}分</font>"

        favorable = '、'.join(h.get('favorable', []))
        unfavorable = '、'.join(h.get('unfavorable', []))
        lines.append(f"{icon} **{h.get('shichen', '')}时** {h.get('shichen_range', '')}  {score_tag}")
        lines.append(f"  宜：{favorable}  忌：{unfavorable}")

    return '\n'.join(lines)


def _build_events_text(events: list) -> str:
    """构建概率事件文本"""
    if not events:
        return ''

    lines = ['\n**🎲 今日概率事件**\n']
    for e in events:
        prob = e.get('probability', 0)
        if prob >= 70:
            tag = f"<font color='green'>{prob}%</font>"
        elif prob >= 40:
            tag = f"<font color='orange'>{prob}%</font>"
        else:
            tag = f"<font color='red'>{prob}%</font>"

        lines.append(f"• {e.get('event', '')}  {tag}")

    return '\n'.join(lines)


def _build_card(fortune_data: dict) -> dict:
    """构建飞书消息卡片"""
    date_str = fortune_data.get("date", "")
    score = fortune_data.get("overall_score", 0)
    career = fortune_data.get("career", {})
    wealth = fortune_data.get("wealth", {})
    love = fortune_data.get("love", {})
    health = fortune_data.get("health", {})
    lucky_color = fortune_data.get("lucky_color", "-")
    lucky_number = fortune_data.get("lucky_number", "-")
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

    # 分数颜色
    if score >= 80:
        score_color = "green"
    elif score >= 60:
        score_color = "orange"
    else:
        score_color = "red"

    elements = [
        {
            "tag": "markdown",
            "content": f"**综合运势**  <font color='{score_color}'>{score}/100 {score_text}</font>",
        },
        {"tag": "hr"},
        {
            "tag": "markdown",
            "content": (
                f"| 💼 事业 | 💰 财运 | 💕 感情 | 🏥 健康 |\n"
                f"| :---: | :---: | :---: | :---: |\n"
                f"| {career.get('score', '-')} | {wealth.get('score', '-')} "
                f"| {love.get('score', '-')} | {health.get('score', '-')} |"
            ),
        },
        {"tag": "hr"},
        {
            "tag": "markdown",
            "content": f"🎨 幸运色：{lucky_color}　🔢 幸运数：{lucky_number}",
        },
    ]

    # 运势解读
    if interpretation:
        if len(interpretation) > 300:
            interpretation = interpretation[:297] + "..."
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "markdown",
            "content": f"**🔮 运势解读**\n{interpretation}",
        })

    # 时辰运势
    hourly_text = _build_hourly_text(hourly_fortunes)
    if hourly_text:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "markdown",
            "content": hourly_text,
        })

    # 概率事件
    events_text = _build_events_text(probability_events)
    if events_text:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "markdown",
            "content": events_text,
        })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"每日运势播报 · {date_str}",
                },
                "template": "red",
            },
            "elements": elements,
        },
    }


def send_fortune_feishu(webhook_url: str, fortune_data: dict) -> bool:
    """发送飞书运势消息"""
    card = _build_card(fortune_data)

    try:
        response = httpx.post(
            webhook_url,
            json=card,
            timeout=10.0,
        )
        result = response.json()
        if result.get("code") == 0:
            logger.info("飞书推送成功")
            return True
        else:
            logger.error("飞书推送失败: %s", result.get("msg"))
            return False
    except httpx.TimeoutException:
        logger.error("飞书推送超时")
        return False
    except Exception as e:
        logger.error("飞书推送异常: %s", e)
        return False
