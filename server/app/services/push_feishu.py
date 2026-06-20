# -*- coding: utf-8 -*-
"""Spec 017: 飞书机器人推送服务"""
import logging

import httpx

logger = logging.getLogger(__name__)


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
            "content": f"**综合运势**  <font color='{score_color}'>{score}/100</font>",
        },
        {"tag": "hr"},
        {
            "tag": "markdown",
            "content": (
                f"| 事业运 | 财运 | 感情运 | 健康运 |\n"
                f"| :---: | :---: | :---: | :---: |\n"
                f"| {career.get('score', '-')} | {wealth.get('score', '-')} "
                f"| {love.get('score', '-')} | {health.get('score', '-')} |"
            ),
        },
        {"tag": "hr"},
        {
            "tag": "markdown",
            "content": f"🍀 幸运色：{lucky_color}　🔢 幸运数：{lucky_number}",
        },
    ]

    if interpretation:
        # 截断过长的解读
        if len(interpretation) > 300:
            interpretation = interpretation[:297] + "..."
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "markdown",
            "content": f"**大师解读**\n{interpretation}",
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
    """发送飞书运势消息

    Args:
        webhook_url: 飞书 Webhook URL
        fortune_data: 运势数据字典

    Returns:
        True 发送成功, False 发送失败
    """
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
