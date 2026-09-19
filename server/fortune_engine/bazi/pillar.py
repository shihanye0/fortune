# -*- coding: utf-8 -*-
"""八字排盘核心算法"""
from lunar_python import Lunar, Solar
from fortune_engine.common.tiangan import Tiangan
from fortune_engine.common.dizhi import Dizhi
from fortune_engine.common.wuxing import Wuxing


# 十神名称映射 (日主五行, 对方五行) → 十神
# 生我为印（正印/偏印），我生为食伤，克我为官杀，我克为财，同我为比劫
TEN_GOD_NAMES = {
    # (关系, 阴阳同异)
    ("同", True): "比肩",
    ("同", False): "劫财",
    ("生", True): "偏印",
    ("生", False): "正印",
    ("泄", True): "食神",
    ("泄", False): "伤官",
    ("克", True): "偏官",
    ("克", False): "正官",
    ("耗", True): "偏财",
    ("耗", False): "正财",
}


def _get_relation(dm_wx: Wuxing, other_wx: Wuxing) -> str:
    """获取日主与他干的关系"""
    from fortune_engine.common.wuxing import sheng, ke
    if dm_wx == other_wx:
        return "同"
    if sheng(other_wx) == dm_wx:  # 对方生日主
        return "生"
    if sheng(dm_wx) == other_wx:  # 日主生对方
        return "泄"
    if ke(other_wx) == dm_wx:  # 对方克日主
        return "克"
    if ke(dm_wx) == other_wx:  # 日主克对方
        return "耗"
    return "同"


def _calc_ten_god(dm_name: str, other_name: str) -> str:
    """计算十神"""
    dm = Tiangan.from_name(dm_name)
    other = Tiangan.from_name(other_name)
    if not dm or not other:
        return "未知"
    relation = _get_relation(dm.wuxing, other.wuxing)
    same_yinyang = dm.yinyang == other.yinyang
    return TEN_GOD_NAMES.get((relation, same_yinyang), "未知")


def _count_five_elements(tg_list: list[str], dz_list: list[str]) -> dict[str, int]:
    """统计四柱天干、地支的可见五行分布。

    藏干和月令旺衰需要单独的权重模型，不能混入简单计数后伪装成
    精确结论；本函数因此只统计四柱中直接可见的八个字。
    """
    counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for name in tg_list:
        tg = Tiangan.from_name(name)
        if tg:
            counts[tg.wuxing.value] += 1
    for name in dz_list:
        dz = Dizhi.from_name(name)
        if dz:
            counts[dz.wuxing.value] += 1
    return counts


def _get_favorable(day_master: str, five_elements: dict[str, int]) -> list[str]:
    """给出基于可见五行计数的基础偏向。

    这是用于日运评分的简化规则，并非包含藏干、月令和格局判断的
    专业喜用神结论。日主偏弱时优先返回“生我”的五行和同类五行；
    原实现误把“我生”的五行当作“生我”，会反向影响每日评分。
    """
    from fortune_engine.common.wuxing import sheng, ke
    dm = Tiangan.from_name(day_master)
    if not dm:
        return []
    dm_wx = dm.wuxing
    dm_count = five_elements.get(dm_wx.value, 0)
    # 生我者：寻找“其所生”为日主的五行。
    generating_wx = next(wx for wx in Wuxing if sheng(wx) == dm_wx)
    # 简单规则：日主五行出现次数 < 2 则喜生扶，>= 2 则喜克泄
    if dm_count < 2:
        # 喜生扶：喜印（生我）和比劫（同我）
        return [generating_wx.value, dm_wx.value]
    else:
        # 喜泄耗：食伤（我生）和财（我克）
        return [sheng(dm_wx).value, ke(dm_wx).value]


def calculate_bazi(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    gender: int = 1,
) -> dict:
    """
    计算八字排盘

    Args:
        birth_year: 出生年
        birth_month: 出生月
        birth_day: 出生日
        birth_hour: 出生时 (0-23)
        gender: 性别 (1=男, 0=女)

    Returns:
        排盘结果字典
    """
    # 1. 阳历转阴历，并通过 EightChar 统一使用库的精确口径：
    # 年、月以节气（含立春）切换，日柱采用该库默认的零点换日口径。
    solar = Solar.fromYmdHms(birth_year, birth_month, birth_day, birth_hour, 0, 0)
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()
    eight_char.setSect(2)

    # 2. 年柱、月柱：使用精确节气口径，而不是农历新年/初一口径。
    year_tg = eight_char.getYearGan()
    year_dz = eight_char.getYearZhi()
    year_pillar = eight_char.getYear()

    month_tg = eight_char.getMonthGan()
    month_dz = eight_char.getMonthZhi()
    month_pillar = eight_char.getMonth()

    # 3. 日柱、时柱：交由同一八字对象处理，避免子时规则不一致。
    day_tg = eight_char.getDayGan()
    day_dz = eight_char.getDayZhi()
    day_pillar = eight_char.getDay()

    hour_tg = eight_char.getTimeGan()
    hour_dz = eight_char.getTimeZhi()
    hour_pillar = eight_char.getTime()

    # 4. 日主
    day_master = day_tg

    # 5. 五行统计（四柱天干 + 地支的可见五行，不含藏干权重）
    tgs = [year_tg, month_tg, day_tg, hour_tg]
    dzs = [year_dz, month_dz, day_dz, hour_dz]
    five_elements = _count_five_elements(tgs, dzs)

    # 6. 十神（年、月、时柱天干相对日主）
    ten_gods = {
        "year": _calc_ten_god(day_master, year_tg),
        "month": _calc_ten_god(day_master, month_tg),
        "day": "日主",
        "hour": _calc_ten_god(day_master, hour_tg),
    }

    # 7. 大运排列：交由 lunar-python 按节气差计算起运时间。
    major_luck_cycles = _calc_luck_cycles(eight_char, gender)

    # 8. 基础五行偏向
    favorable_elements = _get_favorable(day_master, five_elements)

    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "hour_pillar": hour_pillar,
        "day_master": day_master,
        "five_elements": five_elements,
        "ten_gods": ten_gods,
        "major_luck_cycles": major_luck_cycles,
        "favorable_elements": favorable_elements,
    }


def _calc_luck_cycles(eight_char, gender: int) -> list[dict]:
    """计算大运排列和实际起运区间。

    ``getDaYun`` 的第 0 项为出生至起运前的小运区间，干支为空；对外
    仅返回后续八步正式大运，避免把空干支当作一柱展示。
    """
    yun = eight_char.getYun(gender, sect=1)
    da_yun = yun.getDaYun(9)[1:]
    return [
        {
            "start_age": item.getStartAge(),
            "end_age": item.getEndAge(),
            "start_year": item.getStartYear(),
            "end_year": item.getEndYear(),
            "pillar": item.getGanZhi(),
        }
        for item in da_yun
    ]
