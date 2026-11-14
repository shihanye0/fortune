# -*- coding: utf-8 -*-
"""中国大陆夏令时判定。

Port 自 Renhuai123/ziwei-doushu lib/ziwei/dst-cn.ts（MIT License）。
铁律：**只提示、不自动减 1 小时**——无法确认用户报的是夏令时读数还是已换算的
标准时，默默减一小时既可能算错，又会把存量命盘悄悄改掉。判定纯按公历日期、
不看小时，起止日都含（起止日内整天视为夏令时，与通行排盘口径一致）。
"""

# [年, 起月, 起日, 止月, 止日]，起止日都含；与源表逐条对应
XLS_CN = (
    [(y, 5, 1, 9, 30) for y in range(1935, 1952)]
    + [
        (1952, 3, 1, 10, 31),
        (1953, 4, 1, 10, 31),
        (1954, 4, 1, 10, 31),
        (1955, 5, 1, 9, 30),
        (1956, 5, 1, 9, 30),
        (1957, 4, 1, 9, 30),
        (1958, 4, 1, 9, 30),
        (1959, 4, 1, 9, 30),
        (1960, 6, 1, 9, 30),
        (1961, 6, 1, 9, 30),
        (1974, 4, 1, 10, 31),
        (1975, 4, 1, 10, 31),
        (1979, 7, 1, 9, 30),
        (1986, 5, 4, 9, 14),
        (1987, 4, 12, 9, 13),
        (1988, 4, 10, 9, 11),
        (1989, 4, 16, 9, 17),
        (1990, 4, 15, 9, 16),
        (1991, 4, 14, 9, 15),
    ]
)


def is_china_dst(year, month, day):
    """该公历日期是否处于中国大陆夏令时期间（纯按日期判定，不看小时）。"""
    for y, m1, d1, m2, d2 in XLS_CN:
        if year != y:
            continue
        if m1 < month < m2:
            return True
        if month == m1:
            if day >= d1:
                return True
        elif month == m2:
            if day <= d2:
                return True
    return False


def is_china_dst_year(year):
    """该年是否在夏令时表内（用于提前提示）。"""
    return any(row[0] == year for row in XLS_CN)


def china_dst_range(year):
    """该年的夏令时区间文案（起止都含）。不在表内返回 None。"""
    for row in XLS_CN:
        if row[0] == year:
            return {"start": f"{row[1]} 月 {row[2]} 日", "end": f"{row[3]} 月 {row[4]} 日"}
    return None


def china_dst_years():
    """表内覆盖的全部年份（升序）。"""
    return [row[0] for row in XLS_CN]
