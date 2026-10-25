# -*- coding: utf-8 -*-
"""日干支冲煞推算：黄历"今日冲X(XX) 煞X"口径。

规则：
- 冲支 = 日支六冲（相隔六位）；
- 被冲干支的天干 = 日干所克五行中与日干同阴阳的那一个（如甲子日冲戊午：甲木克土，阳土为戊）；
- 煞方 = 日支三合局的三煞方位（申子辰煞南、寅午戌煞北、巳酉丑煞东、亥卯未煞西）。
"""
from fortune_engine.common.dizhi import Dizhi, DIZHI_LIST
from fortune_engine.common.tiangan import Tiangan, TIANGAN_LIST
from fortune_engine.common.wuxing import ke

DIZHI_ZODIAC = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

# 三合局 → 三煞方位
_SHA_DIRECTION = {}
for _branches, _direction in (
    (("申", "子", "辰"), "南"),
    (("寅", "午", "戌"), "北"),
    (("巳", "酉", "丑"), "东"),
    (("亥", "卯", "未"), "西"),
):
    for _branch in _branches:
        _SHA_DIRECTION[_branch] = _direction


def get_day_chongsha(heavenly_stem: str | None, earthly_branch: str | None) -> dict | None:
    """由日干支推冲煞信息；干支缺失或非法时返回 None，调用方直接跳过展示。"""
    if not heavenly_stem or not earthly_branch:
        return None
    try:
        stem = Tiangan.from_name(heavenly_stem)
        branch = Dizhi.from_name(earthly_branch)
    except (KeyError, ValueError):
        return None
    if stem is None or branch is None:
        return None

    branch_idx = DIZHI_LIST.index(branch)
    clash_branch = DIZHI_LIST[(branch_idx + 6) % 12]

    # 日干所克五行（我克者为财），取与日干同阴阳的天干
    target_wx = ke(stem.wuxing)
    clash_stem = next(
        (t for t in TIANGAN_LIST if t.wuxing == target_wx and t.yinyang == stem.yinyang),
        TIANGAN_LIST[0],
    )

    animal = DIZHI_ZODIAC.get(clash_branch.name, "")
    ganzhi = f"{clash_stem.name}{clash_branch.name}"
    sha = _SHA_DIRECTION.get(branch.name, "")
    if not animal or not sha:
        return None

    return {
        "clash_animal": animal,
        "clash_ganzhi": ganzhi,
        "sha_direction": sha,
        "display": f"冲{animal}({ganzhi}) 煞{sha}",
        "display_short": f"冲{animal} 煞{sha}",
    }
