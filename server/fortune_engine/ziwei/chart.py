# -*- coding: utf-8 -*-
"""Ziwei doushu chart engine.

Algorithm ported from iztro (MIT) with conventions confirmed against
Renhuai123/ziwei-doushu (MIT). Key conventions: lunar new year boundary
(zheng-yue-1 changes year, yearDivide='normal'); leap month days 1-15
belong to this month, 16+ to next (fixLeap); late zi hour (23:00-24:00)
stays same-day zi hour; brightness = iztro STARS_INFO (yin-start index).
Deterministic chart first, LLM only interprets.
"""
from datetime import date

from lunar_python import Solar

from fortune_engine.common.dst_cn import is_china_dst

STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
ZODIAC = {"子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
          "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪"}
PALACE_NAMES_ORDER = ("命宫", "父母", "福德", "田宅", "官禄", "仆役",
                      "迁移", "疾厄", "财帛", "子女", "夫妻", "兄弟")
SHICHEN_NAMES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
SHICHEN_RANGES = ("23:00-01:00", "01:00-03:00", "03:00-05:00", "05:00-07:00", "07:00-09:00",
                  "09:00-11:00", "11:00-13:00", "13:00-15:00", "15:00-17:00", "17:00-19:00",
                  "19:00-21:00", "21:00-23:00")

SI_HUA_TABLE = {
    0: ("廉贞", "破军", "武曲", "太阳"),
    1: ("天机", "天梁", "紫微", "太阴"),
    2: ("天同", "天机", "文昌", "廉贞"),
    3: ("太阴", "天同", "巨门", "天机"),
    3: ("太阴", "天同", "天机", "巨门"),  # ding
    4: ("贪狼", "太阴", "右弼", "天机"),  # wu
    5: ("武曲", "贪狼", "天梁", "文曲"),  # ji
    6: ("太阳", "武曲", "太阴", "天同"),  # geng
    7: ("巨门", "太阳", "文曲", "文昌"),  # xin
    8: ("天梁", "紫微", "左辅", "武曲"),  # ren
    9: ("破军", "巨门", "太阴", "贪狼"),  # gui
}

TIANKUI_TABLE = {0: (1, 7), 1: (0, 8), 2: (11, 9), 3: (11, 9),
                 4: (1, 7), 5: (0, 8), 6: (1, 7), 7: (6, 2),
                 8: (3, 5), 9: (3, 5)}
LUCUN_TABLE = {0: 2, 1: 3, 2: 5, 3: 6, 4: 5, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}
TIANMA_TABLE = {2: 8, 6: 8, 10: 8, 8: 2, 0: 2, 4: 2, 5: 11, 9: 11, 1: 11, 11: 5, 3: 5, 7: 5}
MING_ZHU_TABLE = {0: "贪狼", 1: "巨门", 2: "禄存", 3: "文曲", 4: "廉贞", 5: "武曲",
                  6: "破军", 7: "武曲", 8: "廉贞", 9: "文曲", 10: "禄存", 11: "巨门"}
SHEN_ZHU_TABLE = {0: "火星", 6: "火星", 1: "天相", 7: "天相", 2: "天梁", 8: "天梁",
                  3: "天同", 9: "天同", 4: "文昌", 10: "文昌", 5: "天机", 11: "天机"}

# brightness: 12-slot string per star, position 0 = yin palace (palace index 0)
BRIGHTNESS = {
    "紫微": "旺旺得旺庙庙旺旺得旺平庙",
    "天机": "得旺利平庙陷得旺利平庙陷",
    "太阳": "旺庙旺旺旺得得平不陷陷不",
    "武曲": "得利庙平旺庙得利庙平旺庙",
    "天同": "利平平庙陷不旺平平庙旺不",
}
BRIGHTNESS.update({
    "廉贞": "庙平利陷平利庙平利陷平利",
    "天府": "庙得庙得旺庙得旺庙得庙庙",
    "太阴": "旺陷陷陷不不利旺旺庙庙庙",
    "贪狼": "平利庙陷旺庙平利庙陷旺庙",
    "巨门": "庙庙陷旺旺不庙庙陷旺旺不",
})
BRIGHTNESS.update({
    "天相": "庙陷得得庙得庙陷得得庙庙",
    "天梁": "庙庙庙陷庙旺陷得庙陷庙旺",
    "七杀": "庙旺庙平旺庙庙旺庙平旺庙",
    "破军": "得陷旺平庙旺得陷旺平庙旺",
    "文昌": "陷利得庙陷利得庙陷利得庙",
    "文曲": "平旺得庙陷旺得庙陷旺得庙",
    "火星": "庙利陷得庙利陷得庙利陷得",
    "铃星": "庙利陷得庙利陷得庙利陷得",
    "擎羊": "_陷庙_陷庙_陷庙_陷庙",
    "陀罗": "陷_庙陷_庙陷_庙陷_庙",
})

JU_BY_WUXING = {1: 3, 2: 4, 3: 2, 4: 6, 5: 5}
JU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}
TIGER_RULE = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0, 5: 2, 6: 4, 7: 6, 8: 8, 9: 0}


def fix_index(i):
    return i % 12


def clock_hour_to_shichen(hour):
    if hour is None:
        raise ValueError("birth_hour is required")
    return ((hour + 1) // 2) % 12


def solar_to_lunar(y, m, d):
    """Solar to lunar; year ganzhi uses lunar-new-year boundary."""
    solar = Solar.fromYmd(y, m, d)
    lunar = solar.getLunar()
    gz = lunar.getYearInGanZhi()
    return (lunar.getYear(), lunar.getMonth(), lunar.getDay(),
            STEMS.index(gz[0]), BRANCHES.index(gz[1]))


def calc_five_elements_ju(soul_stem, soul_branch):
    stem_num = soul_stem // 2 + 1
    branch_num = (soul_branch % 6) // 2 + 1
    total = stem_num + branch_num
    while total > 5:
        total -= 5
    ju = JU_BY_WUXING[total]
    return ju, JU_NAMES[ju]


def calc_ziwei_start(lunar_day, ju):
    offset = 0
    divisor = lunar_day
    while divisor % ju != 0:
        offset += 1
        divisor += 1
    quotient = (divisor // ju) % 12
    ziwei = quotient - 1
    if offset % 2 == 0:
        ziwei += offset
    else:
        ziwei -= offset
    return fix_index(ziwei)


def _add_star(palaces, branch, name, kind):
    """Add star at branch (zi=0). Palace list index = (branch - 2) % 12."""
    target = palaces[(branch + 10) % 12]
    if any(s["name"] == name for s in target[kind]):
        return
    row = BRIGHTNESS.get(name)
    pi = (branch + 10) % 12  # palace index (yin-start)
    b = row[pi] if row and row[pi] != "_" else None
    target[kind].append({"name": name, "brightness": b, "mutagen": None})


def _place_major_stars(palaces, ziwei_b, tianfu_b):
    """Major stars: ziwei group逆行, tianfu group顺行. Args are BRANCH idx."""
    zw = ("紫微", "天机", None, "太阳", "武曲", "天同", None, None, "廉贞")
    tf = ("天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", None, None, None, "破军")
    for i, name in enumerate(zw):
        if name:
            _add_star(palaces, fix_index(ziwei_b - i), name, "major_stars")
    for i, name in enumerate(tf):
        if name:
            _add_star(palaces, fix_index(tianfu_b + i), name, "major_stars")


def _place_minor_stars(palaces, y_stem, y_branch, month_1based, t):
    """Minor stars: zuo-you/month, chang-qu/hour, kui-yue/lucun/yangtuo/year-stem, ma/year-branch, kongjie/hour, huoling/year-branch-group+hour."""
    m1 = month_1based
    _add_star(palaces, fix_index(4 + m1 - 1), "左辅", "minor_stars")
    _add_star(palaces, fix_index(10 - (m1 - 1)), "右弼", "minor_stars")
    _add_star(palaces, fix_index(10 - t), "文昌", "minor_stars")
    _add_star(palaces, fix_index(4 + t), "文曲", "minor_stars")
    kui, yue = TIANKUI_TABLE[y_stem]
    _add_star(palaces, kui, "天魁", "minor_stars")
    _add_star(palaces, yue, "天钺", "minor_stars")
    lu = LUCUN_TABLE[y_stem]
    _add_star(palaces, lu, "禄存", "minor_stars")
    _add_star(palaces, TIANMA_TABLE[y_branch], "天马", "minor_stars")
    _add_star(palaces, fix_index(11 - t), "地空", "minor_stars")
    _add_star(palaces, fix_index(11 + t), "地劫", "minor_stars")
    huo, ling = {2: (1, 3), 0: (2, 10), 1: (3, 10), 3: (9, 10)}[y_branch % 4]
    _add_star(palaces, fix_index(huo + t), "火星", "minor_stars")
    _add_star(palaces, fix_index(ling + t), "铃星", "minor_stars")
    _add_star(palaces, fix_index(lu + 1), "擎羊", "minor_stars")
    _add_star(palaces, fix_index(lu - 1), "陀罗", "minor_stars")


def _mark_sihua(palaces, y_stem):
    lu, quan, ke, ji = SI_HUA_TABLE[y_stem]
    marks = {"禄": lu, "权": quan, "科": ke, "忌": ji}
    for palace in palaces:
        for kind in ("major_stars", "minor_stars"):
            for s in palace[kind]:
                if s["name"] in marks.values():
                    s["mutagen"] = [k for k, v in marks.items() if v == s["name"]][0]


def _calc_da_xian(soul_p, ju, yang_year, male):
    """Da xian: yang-male/yin-female forward, else backward (iztro getHoroscope)."""
    rows = []
    for i in range(12):
        p = fix_index(soul_p + i) if (yang_year == male) else fix_index(soul_p - i)
        start = ju + 10 * i
        rows.append((p, start, start + 9))
    return rows


def calculate_ziwei(year, month, day, hour, gender, today=None):
    """Main entry. year/month/day solar birth date, hour 0-23, gender 0=F/1=M."""
    if not (isinstance(hour, int) and 0 <= hour <= 23):
        raise ValueError("hour must be 0-23")
    if gender not in (0, 1):
        raise ValueError("gender must be 0/1")
    birth = date(year, month, day)
    shichen = clock_hour_to_shichen(hour)
    ly, lm_signed, ld, y_stem, y_branch = solar_to_lunar(year, month, day)
    is_leap = lm_signed < 0
    abs_lm = abs(lm_signed)
    leap_fix = 1 if (is_leap and ld > 15) else 0
    eff_month = (abs_lm + leap_fix - 1) % 12 + 1
    month_index = (abs_lm - 1 + leap_fix) % 12
    soul_p = (month_index - shichen) % 12
    body_p = (month_index + shichen) % 12
    start_stem = TIGER_RULE[y_stem]
    soul_stem_idx = (start_stem + soul_p) % 10
    ju, ju_name = calc_five_elements_ju(soul_stem_idx, (soul_p + 2) % 12)
    ziwei_p = calc_ziwei_start(ld, ju)  # palace index (yin-start)
    ziwei_b = (ziwei_p + 2) % 12
    tianfu_b = ((12 - ziwei_p) % 12 + 2) % 12
    palaces = []
    for i in range(12):
        palaces.append({
            "name": None, "branch": BRANCHES[(i + 2) % 12],
            "stem": STEMS[(start_stem + i) % 10],
            "major_stars": [], "minor_stars": [],
        })
    _place_major_stars(palaces, ziwei_b, tianfu_b)
    _place_minor_stars(palaces, y_stem, y_branch, eff_month, shichen)
    _mark_sihua(palaces, y_stem)
    for i, p in enumerate(palaces):
        p["name"] = PALACE_NAMES_ORDER[fix_index(i - soul_p)]
    for p, start, end in _calc_da_xian(soul_p, ju, y_branch % 2 == 0, gender == 1):
        palaces[p]["da_xian"] = {"start": start, "end": end}
    for i, p in enumerate(palaces):
        p["is_soul"] = i == soul_p
        p["is_body"] = i == body_p
    ming_zhu = MING_ZHU_TABLE[(soul_p + 2) % 12]
    shen_zhu = SHEN_ZHU_TABLE[y_branch]
    da_xians = [
        {"start_age": s, "end_age": e, "palace_name": palaces[p]["name"], "branch": palaces[p]["branch"]}
        for p, s, e in sorted(_calc_da_xian(soul_p, ju, y_branch % 2 == 0, gender == 1), key=lambda x: x[1])
    ]
    today = today or date.today()
    current_age = today.year - year + 1  # nominal age (xu sui)
    flow_stem_idx = (today.year - 4) % 10
    flow_sihua = SI_HUA_TABLE[flow_stem_idx]
    flow_ming_branch = BRANCHES[(today.year - 4) % 12]
    notes = [
        "排盘口径：农历正月初一换年（主流紫微口径，与八字立春口径不同）",
        "闰月口径：前 15 天归本月、16 起（含 16）归下月",
    ]
    if is_china_dst(year, month, day):
        notes.append(
            "夏令时提示：出生日期处于中国大陆夏令时期，钟表时间比标准时快 1 小时，"
            "可能影响时辰判定（只提示、不自动调整）"
        )
    return {
        "birth": {"solar": f"{year}-{month}-{day}", "shichen": shichen,
                  "shichen_name": SHICHEN_NAMES[shichen] + "时",
                  "shichen_range": SHICHEN_RANGES[shichen],
                  "gender_code": gender, "gender": "男" if gender == 1 else "女"},
        "lunar": {"year": ly, "month": abs_lm, "day": ld, "is_leap": is_leap,
                  "year_ganzhi": STEMS[y_stem] + BRANCHES[y_branch],
                  "zodiac": ZODIAC[BRANCHES[y_branch]]},
        "soul_palace": palaces[soul_p]["branch"],
        "body_palace": palaces[body_p]["branch"],
        "soul_palace_branch_idx": soul_p, "body_palace_branch_idx": body_p,
        "five_elements": ju_name, "ju": ju,
        "ming_zhu": ming_zhu, "shen_zhu": shen_zhu,
        "current_age": current_age,
        "palaces": [
            {"name": p["name"], "branch": p["branch"], "stem": p["stem"],
             "major_stars": p["major_stars"], "minor_stars": p["minor_stars"],
             "da_xian": p["da_xian"], "is_soul": p["is_soul"], "is_body": p["is_body"]}
            for p in palaces
        ],
        "da_xians": da_xians,
        "flow_year": {"year": today.year, "ganzhi": STEMS[flow_stem_idx] + BRANCHES[(today.year - 4) % 12],
                  "ming_gong_branch": flow_ming_branch,
                  "sihua_stars": list(flow_sihua)},
        "notes": notes,
    }
