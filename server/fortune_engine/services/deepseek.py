# -*- coding: utf-8 -*-
"""DeepSeek API 解读服务"""
import re
import httpx
from app.config import settings


def _strip_markdown(text: str) -> str:
    """清除markdown格式标记"""
    if not text:
        return text
    # 移除 ** 加粗
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # 移除 * 斜体
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # 移除 ## 标题
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 移除 - 列表标记（保留内容）
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    # 移除数字列表标记（保留内容）
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

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

## 用户维度偏好
{dimension_preference}

## 任务要求
1. 用专业但易懂的语言解读八字格局
2. 分析事业、财运、感情、健康四个维度，重点展开用户更关注的维度
3. 给出实用建议
4. 字数控制在 300-500 字"""

DAILY_PROMPT = """你是一位精通命理的运势播报师。请根据以下数据生成今日运势播报。

八字概要：{bazi_summary}

今日运势数据：{fortune_data}

用户偏好：{user_feedback_summary}

历史准确率：{accuracy_info}

重要格式要求（必须严格遵守）：
- 禁止使用任何markdown格式符号，如**、##、-、*等
- 禁止使用加粗、斜体等格式标记
- 直接用纯文字描述，像平时聊天一样
- 先用一句话概括今日整体运势走向
- 事业运：结合八字分析今日工作状态、贵人方位、注意事项，3-4句话
- 财运：分析今日财运走向、投资建议、消费提醒，3-4句话
- 感情运：分析今日桃花运、人际互动、情感建议，3-4句话
- 健康运：分析今日身体状态、养生建议、需注意部位，3-4句话
- 最后给出3-5条具体可操作的今日建议（如穿戴颜色、方位、时间段等）
- 语气温和专业，像一位贴心的命理顾问
- 如果历史准确率较低，适当调整解读风格，更注重客观分析
- 总字数控制在400-600字"""


def _call_deepseek(
    prompt: str,
    max_retries: int = 2,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> str | None:
    """调用 LLM API（优先使用用户配置，回退到 .env）"""
    _base_url = base_url or settings.DEEPSEEK_BASE_URL
    _api_key = api_key or settings.DEEPSEEK_API_KEY
    _model = model or "mimo-v2.5"
    # 清理模型名称（去掉 [1M] 等上下文窗口标注）
    if "[" in _model:
        _model = _model.split("[")[0].strip()

    url = f"{_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
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
    dimension_preference: str = "",
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
        dimension_preference: 用户维度偏好文本

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
        dimension_preference=dimension_preference or "暂无偏好数据",
    )

    if user_feedback_summary:
        prompt += f"\n\n## 用户偏好\n{user_feedback_summary}"

    result = _call_deepseek(prompt)
    return _strip_markdown(result) if result else FALLBACK_FORTUNE


def interpret_daily(
    bazi_summary: str,
    daily_fortune: dict,
    user_feedback_summary: str = "",
    accuracy_info: str = "",
    llm_api_key: str | None = None,
    llm_api_url: str | None = None,
    llm_model: str | None = None,
) -> str:
    """
    生成每日运势播报

    Args:
        bazi_summary: 八字概要
        daily_fortune: 每日运势数据
        user_feedback_summary: 用户反馈摘要
        accuracy_info: 历史准确率信息

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
        accuracy_info=accuracy_info or "暂无历史数据",
    )

    result = _call_deepseek(
        prompt,
        api_key=llm_api_key,
        base_url=llm_api_url,
        model=llm_model,
    )
    return _strip_markdown(result) if result else FALLBACK_DAILY


# --- 六爻解读 ---

LIUYAO_PROMPT = """你是一位精通周易六爻的资深卦师。请用专业但易懂的语言解读以下卦象。

占卜问题：{question}

卦象信息：
本卦：{hexagram_name}
上卦：{upper_trigram}（{upper_image}）
下卦：{lower_trigram}（{lower_image}）
六爻：{lines}
变爻位置：{changing_lines}
变卦：{changed_hexagram}

用户八字信息：{bazi_info}

历史验证结果：{outcome_history}

重要格式要求（必须严格遵守）：
- 禁止使用任何markdown格式符号，如**、##、-、*等
- 禁止使用加粗、斜体等格式标记
- 直接用纯文字描述，像平时聊天一样
- 先用一句话概括卦象核心含义
- 解读本卦和变卦的关系
- 结合用户八字分析运势走向
- 针对占卜问题给出具体、可操作的建议
- 如果有历史验证结果，参考过往准确度调整解读信心
- 语气温和专业
- 总字数控制在250-400字"""


def interpret_liuyao(hexagram_data: dict, bazi_info: str = "", outcome_history: str = "") -> str:
    """
    解读六爻卦象

    Args:
        hexagram_data: hexagram.py 生成的卦象数据
        bazi_info: 用户八字信息
        outcome_history: 历史验证结果文本

    Returns:
        解读文字
    """
    from fortune_engine.liuyao.hexagram import TRIGRAM_IMAGE

    question = hexagram_data.get("question") or "总体运势"
    upper = hexagram_data["upper_trigram"]
    lower = hexagram_data["lower_trigram"]
    changed = hexagram_data.get("changed_hexagram")

    prompt = LIUYAO_PROMPT.format(
        question=question,
        hexagram_name=hexagram_data["name"],
        upper_trigram=upper,
        upper_image=TRIGRAM_IMAGE.get(upper, ""),
        lower_trigram=lower,
        lower_image=TRIGRAM_IMAGE.get(lower, ""),
        lines=hexagram_data["lines"],
        changing_lines=hexagram_data.get("changing_lines", []),
        changed_hexagram=changed["name"] if changed else "无变卦",
        bazi_info=bazi_info or "暂无八字信息",
        outcome_history=outcome_history or "暂无历史验证数据",
    )

    result = _call_deepseek(prompt)
    return _strip_markdown(result) if result else "卦象解读暂不可用，请稍后再试。"


# --- 奇门遁甲解读 ---

QIMEN_PROMPT = """你是一位精通奇门遁甲的资深术士。请用专业但易懂的语言解读以下奇门盘面。

问题：{question}

盘面信息：
阴阳遁：{yin_yang}
局数：第{ju_shu}局
时辰：{time}

九宫详情：
{palace_details}

用户八字信息：{bazi_info}

历史验证结果：{outcome_history}

重要格式要求（必须严格遵守）：
- 禁止使用任何markdown格式符号，如**、##、-、*等
- 禁止使用加粗、斜体等格式标记
- 直接用纯文字描述，像平时聊天一样
- 先概括当前盘面的核心格局
- 解读九星、八门、八神的组合含义
- 结合用户八字分析运势走向
- 针对问题给出具体、可操作的建议
- 如果有历史验证结果，参考过往准确度调整解读信心
- 语气温和专业
- 总字数控制在250-400字"""


FALLBACK_LIUYAO = "卦象解读暂不可用，请稍后再试。您可查看卦象数据了解基本信息。"
FALLBACK_QIMEN = "奇门盘面解读暂不可用，请稍后再试。您可查看盘面数据了解基本信息。"


def interpret_qimen(chart_data: dict, question: str = "", bazi_info: str = "", outcome_history: str = "") -> str:
    """
    解读奇门遁甲盘面

    Args:
        chart_data: chart.py 生成的盘面数据
        question: 占卜问题
        bazi_info: 用户八字信息
        outcome_history: 历史验证结果文本

    Returns:
        解读文字
    """
    q = question or "当前时辰总体运势"

    # 格式化九宫详情
    palace_lines = []
    for pid, info in chart_data.get("palace", {}).items():
        palace_lines.append(
            f"  宫{pid}：{info['star']} / {info['gate']} / {info['god']}"
        )

    prompt = QIMEN_PROMPT.format(
        question=q,
        yin_yang=chart_data["yin_yang"],
        ju_shu=chart_data["ju_shu"],
        time=chart_data.get("time", ""),
        palace_details="\n".join(palace_lines),
        bazi_info=bazi_info or "暂无八字信息",
        outcome_history=outcome_history or "暂无历史验证数据",
    )

    result = _call_deepseek(prompt)
    return _strip_markdown(result) if result else FALLBACK_QIMEN
