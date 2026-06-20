# -*- coding: utf-8 -*-
"""奇门遁甲排盘算法（时家奇门简化版）"""
from lunar_python import Solar

# 九星（按洛书顺序）
NINE_STARS = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]

# 八门（按洛书顺序）
EIGHT_GATES = ["休门", "死门", "伤门", "杜门", "开门", "惊门", "生门", "景门"]

# 八神（按洛书顺序）
EIGHT_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# 洛书飞宫顺序
LUOSHU_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6]


def _get_yin_yang_dun(year: int, month: int, day: int) -> tuple[str, int]:
    """
    根据节气确定阴阳遁和局数

    简化规则：
    - 冬至到夏至前：阳遁
    - 夏至到冬至前：阴遁
    - 局数根据节气和日干支确定（简化为月份推算）
    """
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()

    # 简化：根据月份判断
    # 1-6月（冬至到夏至前）：阳遁
    # 7-12月（夏至到冬至前）：阴遁
    if month <= 6:
        yin_yang = "阳遁"
        ju_shu = (month % 9) or 9
    else:
        yin_yang = "阴遁"
        ju_shu = ((month - 6) % 9) or 9

    return yin_yang, ju_shu


def _rotate_list(lst: list, n: int) -> list:
    """列表循环移位"""
    n = n % len(lst)
    return lst[n:] + lst[:n]


def calculate_qimen(year: int, month: int, day: int, hour: int) -> dict:
    """
    奇门遁甲排盘

    Args:
        year: 年
        month: 月
        day: 日
        hour: 时 (0-23)

    Returns:
        排盘结果字典
    """
    # 1. 确定阴阳遁和局数
    yin_yang, ju_shu = _get_yin_yang_dun(year, month, day)

    # 2. 确定时辰序号（0-11）
    shichen_idx = hour // 2

    # 3. 值符落宫（简化：根据局数和时辰推算）
    zhifu_palace = ((ju_shu + shichen_idx) % 9) or 9

    # 4. 九星飞布（从值符落宫开始，按洛书顺序飞布）
    star_start = (zhifu_palace - 1) % 9
    if yin_yang == "阳遁":
        stars = _rotate_list(NINE_STARS, star_start)
    else:
        stars = _rotate_list(NINE_STARS[::-1], star_start)

    # 5. 八门飞布（从值使门落宫开始）
    gate_start = (ju_shu - 1 + shichen_idx) % 9
    if yin_yang == "阳遁":
        gates = _rotate_list(EIGHT_GATES, gate_start % 8)
    else:
        gates = _rotate_list(EIGHT_GATES[::-1], gate_start % 8)
    # 八门只有 8 个，中宫（第 5 宫）用天禽星对应的门
    # 简化：中宫用开门
    gates_reordered = []
    for i in range(9):
        if i == 4:  # 中宫
            gates_reordered.append("开门")
        else:
            idx = i if i < 4 else i - 1
            gates_reordered.append(gates[idx % 8])

    # 6. 八神飞布
    god_start = (zhifu_palace - 1) % 8
    if yin_yang == "阳遁":
        gods = _rotate_list(EIGHT_GODS, god_start)
    else:
        gods = _rotate_list(EIGHT_GODS[::-1], god_start)
    gods_reordered = [gods[i % 8] for i in range(9)]

    # 7. 组装九宫
    palace = {}
    for i in range(9):
        pid = str(i + 1)
        palace[pid] = {
            "star": stars[i],
            "gate": gates_reordered[i],
            "god": gods_reordered[i],
        }

    return {
        "time": f"{year}-{month:02d}-{day:02d} {hour:02d}:00",
        "yin_yang": yin_yang,
        "ju_shu": ju_shu,
        "palace": palace,
    }
