# -*- coding: utf-8 -*-
"""紫微斗数词表与盘面摘要。

星曜关键词 port 自 Renhuai123/ziwei-doushu lib/ziwei/constants.ts 的
STAR_DESCRIPTIONS（MIT License，已逐字核对）。本词表只做"确定性的盘面摘要 +
固定词表"，供 LLM 解读作上下文；解读本身交给 LLM（确定性排盘与生成式解释分层）。
"""

from fortune_engine.ziwei.chart import SI_HUA_TABLE

# 十四主星关键词（来源：Renhuai123 STAR_DESCRIPTIONS，MIT）
STAR_TRAITS = {
    "紫微": {"keywords": "帝王·尊贵·独立", "nature": "中性偏吉", "element": "土"},
    "天机": {"keywords": "智慧·机变·谋略", "nature": "吉星", "element": "木"},
    "太阳": {"keywords": "阳刚·官贵·慷慨", "nature": "吉星", "element": "火"},
    "天府": {"keywords": "财库·稳重·保守", "nature": "吉星", "element": "土"},
    "太阴": {"keywords": "柔美·财富·阴柔", "nature": "吉星", "element": "水"},
    "贪狼": {"keywords": "欲望·桃花·多才", "nature": "中性", "element": "木"},
    "巨门": {"keywords": "口舌·是非·善辩", "nature": "凶中带吉", "element": "水"},
    "天相": {"keywords": "辅佐·行政·印绶", "nature": "吉星", "element": "水"},
    "天梁": {"keywords": "荫护·医药·长辈", "nature": "吉星", "element": "土"},
    "七杀": {"keywords": "将星·果决·孤克", "nature": "凶星", "element": "金"},
    "武曲": {"keywords": "财富·刚毅·果断", "nature": "中性", "element": "金"},
    "天同": {"keywords": "温和·享福·随缘", "nature": "吉星", "element": "水"},
    "廉贞": {"keywords": "才艺·刑囚·桃花", "nature": "凶中带吉", "element": "火"},
    "破军": {"keywords": "开创·变动·破坏", "nature": "凶星", "element": "水"},
}

# 十二宫含义（简明版，自写）
PALACE_MEANINGS = {
    "命宫": "先天性格与一生格局总览",
    "父母": "与长辈父母的缘分和相处",
    "福德": "精神生活、兴趣与福分",
    "田宅": "家宅、不动产与家庭氛围",
    "官禄": "事业发展与工作状态",
    "仆役": "朋友同事等人际支持",
    "迁移": "外出、变动与远行机遇",
    "疾厄": "身体底子与健康关注点",
    "财帛": "钱财进出与理财风格",
    "子女": "子女缘分与创作成果",
    "夫妻": "婚姻感情与亲密关系",
    "兄弟": "兄弟姐妹与平辈助力",
}

SIHUA_MEANINGS = {
    "禄": "机会与资源顺水而来，带来顺利与进益",
    "权": "主导与执行的力量，带来掌控与成就",
    "科": "名声、贵人相助与学习运",
    "忌": "执着、欠债与消耗点，需刻意经营",
}
BRIGHTNESS_NOTES = {
    "庙": "力量最盛，星性充分发挥",
    "旺": "力量强旺，发挥稳定",
    "得": "得地平衡，发挥正常",
    "利": "力量温和，需后天激发",
    "平": "力量平平，随大环境起落",
    "不": "力量偏弱，多一分努力",
    "陷": "力量受限，更需借助对宫与吉星",
}


def build_chart_summary(chart):
    """Deterministic chart summary for the LLM prompt (no interpretation)."""
    b = chart["birth"]
    lines = []
    lines.append(f"出生：公历{b['solar']}，{b['shichen_name']}（{b['shichen_range']}），{b['gender']}")
    lu = chart["lunar"]
    leap = "闰" if lu["is_leap"] else ""
    lines.append(f"农历：{lu['year_ganzhi']}年{leap}{lu['month']}月{lu['day']}日（{lu['zodiac']}年），五行局：{chart['five_elements']}")
    lines.append(f"命宫：{chart['soul_palace']}宫，身宫：{chart['body_palace']}宫，命主：{chart['ming_zhu']}，身主：{chart['shen_zhu']}，当前虚岁 {chart['current_age']}")
    for p in chart["palaces"]:
        parts = []
        for s in p["major_stars"]:
            seg = s["name"]
            if s["brightness"]:
                seg += s["brightness"]
            if s["mutagen"]:
                seg += "化" + s["mutagen"]
        for s in p["minor_stars"]:
            seg = s["name"] + (s["brightness"] or "")
            if s["mutagen"]:
                seg += "化" + s["mutagen"]
            parts.append(seg)
        if not p["major_stars"]:
            parts = ["空宫（借对宫主星）"] + parts
        star_txt = "、".join(parts)
        disp = p["name"] if p["name"].endswith("宫") else p["name"] + "宫"
        lines.append(f"{disp}（{p['branch']}宫干{p['stem']}）：" + star_txt)
    lines.append("大限：" + "、".join(
        f"{d['start_age']}-{d['end_age']}岁行{d['palace_name'] if d['palace_name'].endswith('宫') else d['palace_name'] + '宫'}"
        for d in chart["da_xians"][:6]))
    fy = chart["flow_year"]["sihua_stars"]
    lines.append(f"流年{chart['flow_year']['year']}（{chart['flow_year']['ganzhi']}）四化：禄{fy[0]} 权{fy[1]} 科{fy[2]} 忌{fy[3]}")
    if chart.get("notes"):
        lines.append("口径说明：" + "；".join(chart["notes"]))
    return "\n".join(lines)


def daily_signal(chart, day_stem_idx):
    """Ziwei daily signal: year-stem sihua stars mapped onto natal palaces.

    day_stem_idx: 0-9 (jia..gui). Returns list of dicts; unknown star -> None.
    """
    lu, quan, ke, ji = SI_HUA_TABLE[day_stem_idx]
    wanted = {"禄": lu, "权": quan, "科": ke, "忌": ji}
    by_star = {}
    for p in chart["palaces"]:
        for s in p["major_stars"] + p["minor_stars"]:
            by_star[s["name"]] = p["name"]
    out = []
    for tag in ("禄", "权", "科", "忌"):
        star = wanted[tag]
        palace = by_star.get(star)
        hint = PALACE_MEANINGS.get(palace, "") if palace else ""
        out.append({"type": tag, "star": star, "palace": palace, "hint": hint})
    return out
