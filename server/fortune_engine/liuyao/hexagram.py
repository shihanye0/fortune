# -*- coding: utf-8 -*-
"""六爻起卦算法"""
import secrets
from datetime import datetime

# 八卦名
TRIGRAM_NAMES = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

# 八卦对应五行
TRIGRAM_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦自然象
TRIGRAM_IMAGE = {
    "乾": "天", "兑": "泽", "离": "火", "震": "雷",
    "巽": "风", "坎": "水", "艮": "山", "坤": "地",
}

# 八卦二进制映射（下爻到上爻）
TRIGRAM_BINARY = {
    (1, 1, 1): "乾",
    (1, 1, 0): "兑",
    (1, 0, 1): "离",
    (1, 0, 0): "震",
    (0, 1, 1): "巽",
    (0, 1, 0): "坎",
    (0, 0, 1): "艮",
    (0, 0, 0): "坤",
}

# 64 卦名映射 (上卦, 下卦) → 卦名。名称前两字与上、下卦顺序一致。
HEXAGRAM_MAP = {
    ("乾", "乾"): "乾为天", ("坤", "坤"): "坤为地",
    ("坎", "坎"): "坎为水", ("离", "离"): "离为火",
    ("震", "震"): "震为雷", ("巽", "巽"): "巽为风",
    ("艮", "艮"): "艮为山", ("兑", "兑"): "兑为泽",
    ("乾", "坤"): "天地否", ("坤", "乾"): "地天泰",
    ("坎", "离"): "水火既济", ("离", "坎"): "火水未济",
    ("震", "艮"): "雷山小过", ("艮", "震"): "山雷颐",
    ("巽", "兑"): "风泽中孚", ("兑", "巽"): "泽风大过",
    ("乾", "巽"): "天风姤", ("巽", "乾"): "风天小畜",
    ("乾", "兑"): "天泽履", ("兑", "乾"): "泽天夬",
    ("乾", "离"): "天火同人", ("离", "乾"): "火天大有",
    ("乾", "震"): "天雷无妄", ("震", "乾"): "雷天大壮",
    ("乾", "坎"): "天水讼", ("坎", "乾"): "水天需",
    ("乾", "艮"): "天山遁", ("艮", "乾"): "山天大畜",
    ("坤", "巽"): "地风升", ("巽", "坤"): "风地观",
    ("坤", "兑"): "地泽临", ("兑", "坤"): "泽地萃",
    ("坤", "离"): "地火明夷", ("离", "坤"): "火地晋",
    ("坤", "震"): "地雷复", ("震", "坤"): "雷地豫",
    ("坤", "坎"): "地水师", ("坎", "坤"): "水地比",
    ("坤", "艮"): "地山谦", ("艮", "坤"): "山地剥",
    ("坎", "巽"): "水风井", ("巽", "坎"): "风水涣",
    ("坎", "兑"): "水泽节", ("兑", "坎"): "泽水困",
    ("坎", "震"): "水雷屯", ("震", "坎"): "雷水解",
    ("坎", "艮"): "水山蹇", ("艮", "坎"): "山水蒙",
    ("离", "巽"): "火风鼎", ("巽", "离"): "风火家人",
    ("离", "兑"): "火泽睽", ("兑", "离"): "泽火革",
    ("离", "震"): "火雷噬嗑", ("震", "离"): "雷火丰",
    ("离", "艮"): "火山旅", ("艮", "离"): "山火贲",
    ("震", "巽"): "雷风恒", ("巽", "震"): "风雷益",
    ("震", "兑"): "雷泽归妹", ("兑", "震"): "泽雷随",
    ("巽", "艮"): "风山渐", ("艮", "巽"): "山风蛊",
    ("艮", "兑"): "山泽损", ("兑", "艮"): "泽山咸",
}


# 六十四卦卦义速查：tendency ∈ 吉 / 平 / 慎，advice 为一句话行动建议
HEXAGRAM_MEANING = {
    "乾为天": {"tendency": "吉", "advice": "刚健进取，宜主动担当"},
    "坤为地": {"tendency": "平", "advice": "厚德包容，宜顺势配合"},
    "坎为水": {"tendency": "慎", "advice": "险阻重重，宜守不宜进"},
    "离为火": {"tendency": "平", "advice": "光明依附，宜借势明断"},
    "震为雷": {"tendency": "平", "advice": "动而有应，宜应变不宜拖延"},
    "巽为风": {"tendency": "平", "advice": "顺势而入，宜沟通协商"},
    "艮为山": {"tendency": "慎", "advice": "止于当止，宜停顿蓄力"},
    "兑为泽": {"tendency": "吉", "advice": "喜悦相通，宜交流联谊"},
    "天地否": {"tendency": "慎", "advice": "闭塞不通，宜守成不宜冒进"},
    "地天泰": {"tendency": "吉", "advice": "三阳开泰，宜推进合作"},
    "水火既济": {"tendency": "吉", "advice": "大功将成，宜防盛极生变"},
    "火水未济": {"tendency": "慎", "advice": "事未成局，宜蓄力待时"},
    "雷山小过": {"tendency": "平", "advice": "小有过越，宜小事不宜大举"},
    "山雷颐": {"tendency": "平", "advice": "养生蓄德，宜学习进补"},
    "风泽中孚": {"tendency": "吉", "advice": "诚信感通，宜立约践诺"},
    "泽风大过": {"tendency": "慎", "advice": "过度承载，宜减压减负"},
    "天风姤": {"tendency": "平", "advice": "不期而遇，宜辨析是非"},
    "风天小畜": {"tendency": "吉", "advice": "小有蓄积，宜筹备储蓄"},
    "天泽履": {"tendency": "平", "advice": "履险如夷，宜循礼慎行"},
    "泽天夬": {"tendency": "吉", "advice": "决断去害，宜了断旧事"},
    "天火同人": {"tendency": "吉", "advice": "同心协力，宜结盟共事"},
    "火天大有": {"tendency": "吉", "advice": "大有所获，宜分享成果"},
    "天雷无妄": {"tendency": "平", "advice": "顺其自然，忌妄动强求"},
    "雷天大壮": {"tendency": "吉", "advice": "声势正盛，宜乘势而上"},
    "天水讼": {"tendency": "慎", "advice": "争讼不利，宜和解避争"},
    "水天需": {"tendency": "平", "advice": "待时而动，宜耐心准备"},
    "天山遁": {"tendency": "慎", "advice": "退避为上，宜抽身远纷扰"},
    "山天大畜": {"tendency": "吉", "advice": "大有蓄养，宜积累进修"},
    "地风升": {"tendency": "吉", "advice": "上升之象，宜求职晋级"},
    "风地观": {"tendency": "平", "advice": "观察审视，宜调研观望"},
    "地泽临": {"tendency": "吉", "advice": "居高临下，宜率领管理"},
    "泽地萃": {"tendency": "吉", "advice": "聚集英才，宜聚会理财"},
    "地火明夷": {"tendency": "慎", "advice": "光明受挫，宜韬光养晦"},
    "火地晋": {"tendency": "吉", "advice": "晋升明进，宜展示才能"},
    "地雷复": {"tendency": "吉", "advice": "一阳来复，宜重启旧事"},
    "雷地豫": {"tendency": "吉", "advice": "顺而快乐，宜宴乐放松"},
    "地水师": {"tendency": "平", "advice": "兴师动众，宜统御有方"},
    "水地比": {"tendency": "吉", "advice": "亲比相助，宜求助结盟"},
    "水风井": {"tendency": "平", "advice": "井养不穷，宜守成分享"},
    "风水涣": {"tendency": "慎", "advice": "涣散离析，宜聚力破局"},
    "水泽节": {"tendency": "平", "advice": "节制有度，宜理财律己"},
    "泽水困": {"tendency": "慎", "advice": "困顿难行，宜守静待援"},
    "水雷屯": {"tendency": "慎", "advice": "万事起头难，宜稳扎稳打"},
    "雷水解": {"tendency": "吉", "advice": "疑难消解，宜处理积案"},
    "水山蹇": {"tendency": "慎", "advice": "前路艰难，宜退守求援"},
    "山水蒙": {"tendency": "平", "advice": "蒙昧待启，宜求教学习"},
    "火风鼎": {"tendency": "吉", "advice": "鼎新革故，宜开创新局"},
    "风火家人": {"tendency": "平", "advice": "家道内外，宜顾家修睦"},
    "火泽睽": {"tendency": "慎", "advice": "乖背离心，宜求同存异"},
    "泽火革": {"tendency": "吉", "advice": "变革之时，宜除旧布新"},
    "火雷噬嗑": {"tendency": "平", "advice": "咬合除梗，宜断决纠纷"},
    "雷火丰": {"tendency": "吉", "advice": "丰盛光大，宜趁热打铁"},
    "火山旅": {"tendency": "平", "advice": "旅途在外，宜顺势流转"},
    "山火贲": {"tendency": "平", "advice": "文饰其表，宜包装展示"},
    "雷风恒": {"tendency": "平", "advice": "恒久之道，宜坚持习惯"},
    "风雷益": {"tendency": "吉", "advice": "损上益下，宜投资助人"},
    "雷泽归妹": {"tendency": "慎", "advice": "名分未正，宜慎对承诺"},
    "泽雷随": {"tendency": "吉", "advice": "随时而安，宜随喜配合"},
    "风山渐": {"tendency": "平", "advice": "循序渐进，宜按部就班"},
    "山风蛊": {"tendency": "慎", "advice": "积弊需整，宜整顿清理"},
    "山泽损": {"tendency": "平", "advice": "损己利人，宜舍小谋大"},
    "泽山咸": {"tendency": "吉", "advice": "心灵感应，宜表白联谊"},
    "地山谦": {"tendency": "吉", "advice": "谦而有终，宜低调礼让"},
    "山地剥": {"tendency": "慎", "advice": "剥落削减，宜收缩防守"},
}


def _lines_to_trigram(lines: list[int]) -> str:
    """三爻转卦名（阴=0, 阳=1）"""
    binary = tuple(1 if l % 2 == 1 else 0 for l in lines)
    return TRIGRAM_BINARY.get(binary, "乾")


def _get_hexagram_name(upper: str, lower: str) -> str:
    """获取卦名"""
    return HEXAGRAM_MAP.get((upper, lower), f"{TRIGRAM_IMAGE[upper]}{TRIGRAM_IMAGE[lower]}")


def _coin_toss() -> int:
    """铜钱法单爻：三枚铜钱，正面=3 反面=2，求和"""
    total = sum(secrets.choice([2, 3]) for _ in range(3))
    # 6=老阴, 7=少阳, 8=少阴, 9=老阳
    return total  # 2+2+2=6, 2+2+3=7, 2+3+3=8, 3+3+3=9


def coin_divination(question: str) -> dict:
    """
    铜钱法起卦

    Args:
        question: 占卜问题

    Returns:
        卦象数据
    """
    # 生成六爻
    lines = [_coin_toss() for _ in range(6)]

    # 本卦
    upper = _lines_to_trigram(lines[3:6])
    lower = _lines_to_trigram(lines[0:3])
    name = _get_hexagram_name(upper, lower)

    # 变爻（老阴=6 和老阳=9）
    changing_indexes = [i for i, l in enumerate(lines) if l in (6, 9)]

    # 变卦
    changed_lines = lines.copy()
    for i in changing_indexes:
        changed_lines[i] = 9 if lines[i] == 6 else 6  # 老阴变老阳，老阳变老阴

    changed_upper = _lines_to_trigram(changed_lines[3:6])
    changed_lower = _lines_to_trigram(changed_lines[0:3])
    changed_name = _get_hexagram_name(changed_upper, changed_lower)

    return {
        "question": question,
        "method": "coin",
        "name": name,
        "upper_trigram": upper,
        "lower_trigram": lower,
        "lines": lines,
        "changing_lines": [i + 1 for i in changing_indexes],
        "changed_hexagram": {
            "name": changed_name,
            "upper_trigram": changed_upper,
            "lower_trigram": changed_lower,
            "lines": changed_lines,
        } if changing_indexes else None,
    }


def time_divination(question: str, year: int, month: int, day: int, hour: int) -> dict:
    """
    时间起卦（梅花易数）

    上卦 = (年 + 月 + 日) % 8
    下卦 = (年 + 月 + 日 + 时) % 8
    变爻 = (年 + 月 + 日 + 时) % 6
    """
    upper_idx = (year + month + day) % 8
    lower_idx = (year + month + day + hour) % 8
    changing_idx = (year + month + day + hour) % 6

    upper = TRIGRAM_NAMES[upper_idx]
    lower = TRIGRAM_NAMES[lower_idx]
    name = _get_hexagram_name(upper, lower)

    # 生成六爻（时间法固定为少阳/少阴）
    lines = []
    for i in range(6):
        # 根据上下卦推导
        if i < 3:
            tg_binary = list(TRIGRAM_BINARY.keys())[list(TRIGRAM_BINARY.values()).index(lower)]
            lines.append(7 if tg_binary[i] == 1 else 8)
        else:
            tg_binary = list(TRIGRAM_BINARY.keys())[list(TRIGRAM_BINARY.values()).index(upper)]
            lines.append(7 if tg_binary[i - 3] == 1 else 8)

    # 变爻
    changing = [changing_idx]

    # 变卦
    changed_lines = lines.copy()
    changed_lines[changing_idx] = 9 if lines[changing_idx] == 7 else 6
    # 变后还要变
    changed_lines[changing_idx] = 8 if changed_lines[changing_idx] == 9 else 7

    changed_upper = _lines_to_trigram(changed_lines[3:6])
    changed_lower = _lines_to_trigram(changed_lines[0:3])
    changed_name = _get_hexagram_name(changed_upper, changed_lower)

    return {
        "question": question,
        "method": "time",
        "name": name,
        "upper_trigram": upper,
        "lower_trigram": lower,
        "lines": lines,
        "changing_lines": [changing_idx + 1],
        "changed_hexagram": {
            "name": changed_name,
            "upper_trigram": changed_upper,
            "lower_trigram": changed_lower,
            "lines": changed_lines,
        },
    }


def daily_hexagram(user_key: int, year: int, month: int, day: int) -> dict:
    """每日一卦：时间起卦按用户区分，同用户同一天结果稳定，附卦义与建议。

    Args:
        user_key: 用户标识（如 user_id），用于让不同用户得到不同的当日卦
        year/month/day: 公历日期
    """
    result = time_divination("今日运势", year, month, day, user_key % 12)
    meaning = HEXAGRAM_MEANING.get(result["name"], {"tendency": "平", "advice": "守常即安"})
    changed = result.get("changed_hexagram") or {}
    return {
        "name": result["name"],
        "upper_trigram": result["upper_trigram"],
        "lower_trigram": result["lower_trigram"],
        "upper_image": TRIGRAM_IMAGE[result["upper_trigram"]],
        "lower_image": TRIGRAM_IMAGE[result["lower_trigram"]],
        "changing_lines": result.get("changing_lines", []),
        "changed_name": changed.get("name", ""),
        "tendency": meaning["tendency"],
        "advice": meaning["advice"],
    }
