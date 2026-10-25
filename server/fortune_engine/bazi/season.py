# -*- coding: utf-8 -*-
"""节气换月提醒：月令以节为准，节气当日/前一日生成换挡提示。

getJieQi() 仅在节气当天返回名称（节与中气都会返回），此处只取
十二"节"（换月节气），中气（雨水/春分等）不换月令，不提示。
"""
from datetime import date, timedelta

from lunar_python import Solar

# 十二节 → 月支
JIEQI_MONTH_ZHI = {
    "立春": "寅", "惊蛰": "卯", "清明": "辰", "立夏": "巳",
    "芒种": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}

_MONTH_ZHI_WUXING = {
    "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水", "子": "水", "丑": "土",
}

_SEASON_TONE = {
    "木": "生发之气渐盛，宜启动新计划",
    "火": "阳气升腾，宜展示与推进",
    "土": "沉潜厚积，宜整理与夯实",
    "金": "收敛肃杀，宜聚焦做减法",
    "水": "闭藏之时，宜蓄力静养、谋定后动",
}


def get_season_note(today: date) -> str | None:
    """节气前一日返回"明日X"，节气当日返回"今日X"；非换月节气日返回 None。"""
    for offset, when in ((1, "明日"), (0, "今日")):
        day = today + timedelta(days=offset)
        jieqi = Solar.fromYmd(day.year, day.month, day.day).getLunar().getJieQi()
        zhi = JIEQI_MONTH_ZHI.get(jieqi or "")
        if not zhi:
            continue
        wx = _MONTH_ZHI_WUXING[zhi]
        return f"{when}{jieqi}，月令转入{zhi}月（{wx}旺），{_SEASON_TONE[wx]}。"
    return None
