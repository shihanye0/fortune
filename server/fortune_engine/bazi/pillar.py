# -*- coding: utf-8 -*-
"""八字排盘核心算法"""
from lunar_python import Lunar, Solar
from fortune_engine.common.tiangan import Tiangan, TIANGAN_LIST
from fortune_engine.common.dizhi import Dizhi, DIZHI_LIST
from fortune_engine.common.wuxing import Wuxing
from fortune_engine.common.shichen import hour_to_shichen


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


def _count_five_elements(tg_list: list[str]) -> dict[str, int]:
    """统计天干的五行分布"""
    counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for name in tg_list:
        tg = Tiangan.from_name(name)
        if tg:
            counts[tg.wuxing.value] += 1
    return counts


def _get_favorable(day_master: str, five_elements: dict[str, int]) -> list[str]:
    """简单喜用神判断：日主弱则喜生扶，强则喜克泄"""
    from fortune_engine.common.wuxing import sheng, ke
    dm = Tiangan.from_name(day_master)
    if not dm:
        return []
    dm_wx = dm.wuxing
    dm_count = five_elements.get(dm_wx.value, 0)
    # 生我者
    bi_wx = [k for k, v in Wuxing.__members__.items() if sheng(v) == dm_wx]
    # 简单规则：日主五行出现次数 < 2 则喜生扶，>= 2 则喜克泄
    if dm_count < 2:
        # 喜生扶：喜印（生我）和比劫（同我）
        return [dm_wx.value, sheng(dm_wx).value]
    else:
        # 喜克泄：喜官杀（克我）、食伤（我生）、财（我克）
        return [ke(dm_wx).value, sheng(dm_wx).value]


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
    # 1. 阳历转阴历
    solar = Solar.fromYmdHms(birth_year, birth_month, birth_day, birth_hour, 0, 0)
    lunar = solar.getLunar()

    # 2. 年柱：以立春为界（lunar-python 已处理）
    year_tg = lunar.getYearGan()
    year_dz = lunar.getYearZhi()
    year_pillar = year_tg + year_dz

    # 3. 月柱：以节气为界
    month_tg = lunar.getMonthGan()
    month_dz = lunar.getMonthZhi()
    month_pillar = month_tg + month_dz

    # 4. 日柱
    day_tg = lunar.getDayGan()
    day_dz = lunar.getDayZhi()
    day_pillar = day_tg + day_dz

    # 5. 时柱：根据日干和时辰推算
    #    子时换日规则：23:00 后算次日子时（早子时）
    hour_branch = hour_to_shichen(birth_hour)
    # 时干推算：日干 × 2 + 时辰地支序号，取天干
    day_tg_idx = TIANGAN_LIST.index(Tiangan.from_name(day_tg))
    dz_idx = DIZHI_LIST.index(Dizhi.from_name(hour_branch))
    hour_tg_idx = (day_tg_idx * 2 + dz_idx) % 10
    hour_tg = TIANGAN_LIST[hour_tg_idx].name
    hour_pillar = hour_tg + hour_branch

    # 6. 日主
    day_master = day_tg

    # 7. 五行统计（四柱天干）
    tgs = [year_tg, month_tg, day_tg, hour_tg]
    five_elements = _count_five_elements(tgs)

    # 8. 十神（年、月、时柱天干相对日主）
    ten_gods = {
        "year": _calc_ten_god(day_master, year_tg),
        "month": _calc_ten_god(day_master, month_tg),
        "day": "日主",
        "hour": _calc_ten_god(day_master, hour_tg),
    }

    # 9. 大运排列
    major_luck_cycles = _calc_luck_cycles(
        birth_year, birth_month, birth_day, birth_hour, gender
    )

    # 10. 喜用神
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


def _calc_luck_cycles(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, gender: int,
) -> list[dict]:
    """计算大运排列"""
    solar = Solar.fromYmdHms(birth_year, birth_month, birth_day, birth_hour, 0, 0)
    lunar = solar.getLunar()

    year_tg = lunar.getYearGan()
    month_tg = lunar.getMonthGan()
    month_dz = lunar.getMonthZhi()

    # 判断年干阴阳
    year_tg_obj = Tiangan.from_name(year_tg)
    is_yang = year_tg_obj.yinyang == "阳"

    # 阳年男/阴年女 → 顺排；阴年男/阳年女 → 逆排
    forward = (is_yang and gender == 1) or (not is_yang and gender == 0)

    # 月柱的干支索引
    month_tg_idx = TIANGAN_LIST.index(Tiangan.from_name(month_tg))
    month_dz_idx = DIZHI_LIST.index(Dizhi.from_name(month_dz))

    cycles = []
    for i in range(1, 9):  # 8 步大运
        if forward:
            tg_idx = (month_tg_idx + i) % 10
            dz_idx = (month_dz_idx + i) % 12
        else:
            tg_idx = (month_tg_idx - i) % 10
            dz_idx = (month_dz_idx - i) % 12

        cycles.append({
            "start_age": i * 10,  # 简化：每步大运 10 年
            "pillar": TIANGAN_LIST[tg_idx].name + DIZHI_LIST[dz_idx].name,
        })

    return cycles
