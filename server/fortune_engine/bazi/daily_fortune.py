# -*- coding: utf-8 -*-
"""每日运势推算：基于八字与流日干支的五行生克"""
from lunar_python import Solar
from fortune_engine.common.tiangan import Tiangan
from fortune_engine.common.dizhi import Dizhi
from fortune_engine.common.wuxing import Wuxing, sheng, ke


# 五行 → 幸运色
WX_LUCKY_COLOR = {
    Wuxing.JIN: "白色、金色",
    Wuxing.MU: "绿色、青色",
    Wuxing.SHUI: "黑色、蓝色",
    Wuxing.HUO: "红色、紫色",
    Wuxing.TU: "黄色、棕色",
}

# 五行 → 幸运数字
WX_LUCKY_NUMBER = {
    Wuxing.JIN: "4, 9",
    Wuxing.MU: "3, 8",
    Wuxing.SHUI: "1, 6",
    Wuxing.HUO: "2, 7",
    Wuxing.TU: "5, 0",
}

# 五行 → 幸运方位
WX_LUCKY_DIRECTION = {
    Wuxing.JIN: "西方",
    Wuxing.MU: "东方",
    Wuxing.SHUI: "北方",
    Wuxing.HUO: "南方",
    Wuxing.TU: "中央",
}

# 十神 → 运势基调
SHEN_SCORE_MAP = {
    "比肩": 3, "劫财": 3,
    "正印": 4, "偏印": 3,
    "食神": 4, "伤官": 2,
    "正官": 3, "偏官": 2,
    "正财": 4, "偏财": 3,
}


def _score_from_relation(dm_wx: Wuxing, other_wx: Wuxing) -> int:
    """根据日主与流日天干的五行关系打分 (1-5)"""
    if dm_wx == other_wx:
        return 3  # 比肩
    if sheng(other_wx) == dm_wx:
        return 4  # 印（生我）
    if sheng(dm_wx) == other_wx:
        return 3  # 食伤（我生）
    if ke(other_wx) == dm_wx:
        return 2  # 官杀（克我）
    if ke(dm_wx) == other_wx:
        return 4  # 财（我克）
    return 3


def _score_to_detail(score: int, dimension: str) -> str:
    """评分转文字描述"""
    details = {
        1: f"{dimension}运势低迷，宜守不宜攻",
        2: f"{dimension}运势一般，谨慎为上",
        3: f"{dimension}运势平稳，按部就班",
        4: f"{dimension}运势不错，可积极把握",
        5: f"{dimension}运势极佳，大有可为",
    }
    return details.get(score, "")


def calculate_daily_fortune(
    bazi: dict,
    year: int,
    month: int,
    day: int,
) -> dict:
    """
    推算每日运势

    Args:
        bazi: 八字排盘结果（来自 calculate_bazi）
        year: 查询年
        month: 查询月
        day: 查询日

    Returns:
        运势结果字典
    """
    # 1. 获取当日干支
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()
    day_tg = lunar.getDayGan()
    day_dz = lunar.getDayZhi()

    # 2. 日主五行
    dm = Tiangan.from_name(bazi["day_master"])
    dm_wx = dm.wuxing

    # 3. 流日天干五行
    flow_tg = Tiangan.from_name(day_tg)
    flow_wx = flow_tg.wuxing

    # 4. 基础评分（日主与流日天干的关系）
    base_score = _score_from_relation(dm_wx, flow_wx)

    # 5. 四维评分（加减微调）
    fav = set(bazi.get("favorable_elements", []))
    flow_is_fav = flow_wx.value in fav

    # 流日五行是喜用神则加分
    bonus = 1 if flow_is_fav else 0

    career_score = min(5, max(1, base_score + bonus))
    wealth_score = min(5, max(1, base_score + (1 if flow_wx == Wuxing.JIN or flow_wx == Wuxing.TU else 0)))
    love_score = min(5, max(1, base_score + (1 if flow_wx == Wuxing.MU or flow_wx == Wuxing.HUO else 0)))
    health_score = min(5, max(1, base_score + (1 if flow_wx == Wuxing.SHUI else -1)))

    overall = round((career_score + wealth_score + love_score + health_score) / 4)

    # 6. 幸运信息（基于喜用神）
    primary_fav = Wuxing(fav.pop()) if fav else dm_wx
    # 取第一个喜用神，如果没有则用日主五行

    return {
        "heavenly_stem": day_tg,
        "earthly_branch": day_dz,
        "overall_score": overall,
        "career_fortune": {"score": career_score, "detail": _score_to_detail(career_score, "事业")},
        "wealth_fortune": {"score": wealth_score, "detail": _score_to_detail(wealth_score, "财运")},
        "love_fortune": {"score": love_score, "detail": _score_to_detail(love_score, "感情")},
        "health_fortune": {"score": health_score, "detail": _score_to_detail(health_score, "健康")},
        "lucky_color": WX_LUCKY_COLOR.get(primary_fav, ""),
        "lucky_number": WX_LUCKY_NUMBER.get(primary_fav, ""),
        "lucky_direction": WX_LUCKY_DIRECTION.get(primary_fav, ""),
    }
