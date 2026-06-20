# -*- coding: utf-8 -*-
"""DeepSeek API 解读服务"""
import httpx
from app.config import settings

# 降级结果
FALLBACK_FORTUNE = "今日解读暂不可用，请稍后再试。您可查看基础运势数据了解今日概况。"
FALLBACK_DAILY = "今日详细解读暂不可用，请查看运势评分了解今日概况。"

# Prompt 模板
FORTUNE_PROMPT = """你是一位精通周易、八字命理的资深命理师。请用专业但易懂的语言解读以下八字信息。

## 用户信息
- 性别：{gender}
- 生辰：{birth_info}
- 八字：{bazi}
- 五行：{five_elements}
- 喜用神：{favorable_elements}

## 任务要求
1. 用专业但易懂的语言解读八字格局
2. 分析事业、财运、感情、健康四个维度
3. 给出实用建议
4. 字数控制在 300-500 字"""

DAILY_PROMPT = """你是一位精通命理的运势播报师。请根据以下数据生成今日运势播报。

## 八字概要
{bazi_summary}

## 今日运势数据
{fortune_data}

## 用户偏好
{user_feedback_summary}

## 任务要求
1. 先总评今日运势
2. 分事业、财运、感情、健康四维度展开
3. 给出 2-3 条实用建议
4. 字数控制在 200-400 字"""


def _call_deepseek(prompt: str, max_retries: int = 2) -> str | None:
    """调用 DeepSeek API"""
    url = f"{settings.DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    for attempt in range(max_retries + 1):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.TimeoutException, httpx.HTTPError, Exception):
            if attempt == max_retries:
                return None
            continue
    return None


def interpret_fortune(
    gender: str,
    birth_info: str,
    bazi: str,
    five_elements: dict,
    favorable_elements: list[str],
    user_feedback_summary: str = "",
) -> str:
    """
    解读八字命理

    Args:
        gender: 性别
        birth_info: 出生信息
        bazi: 八字四柱
        five_elements: 五行分布
        favorable_elements: 喜用神
        user_feedback_summary: 用户历史反馈摘要

    Returns:
        解读文字
    """
    fe_str = "、".join(f"{k}{v}个" for k, v in five_elements.items())
    fav_str = "、".join(favorable_elements) if favorable_elements else "待分析"

    prompt = FORTUNE_PROMPT.format(
        gender=gender,
        birth_info=birth_info,
        bazi=bazi,
        five_elements=fe_str,
        favorable_elements=fav_str,
    )

    if user_feedback_summary:
        prompt += f"\n\n## 用户偏好\n{user_feedback_summary}"

    result = _call_deepseek(prompt)
    return result or FALLBACK_FORTUNE


def interpret_daily(
    bazi_summary: str,
    daily_fortune: dict,
    user_feedback_summary: str = "",
) -> str:
    """
    生成每日运势播报

    Args:
        bazi_summary: 八字概要
        daily_fortune: 每日运势数据
        user_feedback_summary: 用户反馈摘要

    Returns:
        运势播报文字
    """
    # 格式化运势数据
    fortune_lines = []
    if "overall_score" in daily_fortune:
        fortune_lines.append(f"综合评分：{daily_fortune['overall_score']}/5")
    for dim in ["career_fortune", "wealth_fortune", "love_fortune", "health_fortune"]:
        if dim in daily_fortune:
            d = daily_fortune[dim]
            name = {"career": "事业", "wealth": "财运", "love": "感情", "health": "健康"}[dim.split("_")[0]]
            fortune_lines.append(f"{name}：{d.get('score', '-')}/5 — {d.get('detail', '')}")

    prompt = DAILY_PROMPT.format(
        bazi_summary=bazi_summary,
        fortune_data="\n".join(fortune_lines),
        user_feedback_summary=user_feedback_summary or "无特殊偏好",
    )

    result = _call_deepseek(prompt)
    return result or FALLBACK_DAILY
