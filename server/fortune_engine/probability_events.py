# -*- coding: utf-8 -*-
"""概率事件推算引擎：基于八字+运势推算今日可能发生的具体事件"""
from datetime import date
from fortune_engine.common.wuxing import Wuxing, sheng, ke, SHENG_MAP


# 事件模板库（按五行+十神分类）- 扩展版
EVENT_TEMPLATES = {
    # 事业类
    "career": {
        "high": [
            {"event": "收到面试邀请", "desc": "可能收到心仪公司的面试通知或项目合作邀请"},
            {"event": "获得领导赏识", "desc": "工作表现被上级注意到，有升职加薪机会"},
            {"event": "项目取得突破", "desc": "困扰已久的难题找到解决方案"},
            {"event": "贵人引荐机会", "desc": "有前辈或朋友介绍好的工作机会"},
            {"event": "创意获得认可", "desc": "你的想法或提案得到团队支持"},
            {"event": "合作谈判顺利", "desc": "商务洽谈进展顺利，有望达成协议"},
        ],
        "medium": [
            {"event": "工作平稳推进", "desc": "日常事务顺利，无大波折"},
            {"event": "团队协作顺畅", "desc": "与同事配合默契，效率提升"},
            {"event": "学习新技能", "desc": "适合学习新知识或工具"},
            {"event": "整理工作计划", "desc": "适合梳理思路，制定计划"},
        ],
        "low": [
            {"event": "注意职场人际", "desc": "可能遇到小摩擦，保持低调"},
            {"event": "避免冲动决策", "desc": "重要决定建议延后，多思考"},
            {"event": "谨慎处理文件", "desc": "签约或重要文件需仔细审核"},
        ],
    },
    # 财运类
    "wealth": {
        "high": [
            {"event": "意外收入入账", "desc": "可能收到奖金、红包或投资回报"},
            {"event": "投资机会显现", "desc": "有不错的理财机会，可适当关注"},
            {"event": "省钱好deal出现", "desc": "遇到心仪商品打折或优惠"},
            {"event": "副业收入增加", "desc": "兼职或副业有额外进账"},
            {"event": "债务有望收回", "desc": "借出的钱可能被归还"},
            {"event": "理财收益增长", "desc": "之前的投资可能有好消息"},
        ],
        "medium": [
            {"event": "收支平衡", "desc": "财运平稳，无大起大落"},
            {"event": "理性消费日", "desc": "适合做预算规划"},
            {"event": "储蓄计划推进", "desc": "适合存钱或调整理财方案"},
        ],
        "low": [
            {"event": "谨慎投资", "desc": "不宜大额投资或借贷"},
            {"event": "避免冲动消费", "desc": "购物前多考虑是否必要"},
            {"event": "防范诈骗", "desc": "警惕高回报诱惑"},
        ],
    },
    # 感情类
    "love": {
        "high": [
            {"event": "桃花运旺盛", "desc": "可能遇到心仪对象或收到表白"},
            {"event": "感情升温", "desc": "与伴侣关系更加亲密"},
            {"event": "收到惊喜", "desc": "可能收到礼物或浪漫安排"},
            {"event": "旧情复燃", "desc": "可能收到前任消息或偶遇"},
            {"event": "表白成功率高", "desc": "适合表达心意"},
            {"event": "约会顺利", "desc": "约会或聚会氛围融洽"},
        ],
        "medium": [
            {"event": "感情平稳", "desc": "适合平淡温馨的相处"},
            {"event": "社交活跃", "desc": "朋友聚会增多，人脉拓展"},
            {"event": "增进了解", "desc": "适合深入交流，了解彼此"},
        ],
        "low": [
            {"event": "避免争执", "desc": "容易因小事产生误会"},
            {"event": "给彼此空间", "desc": "适当保持距离，避免过度纠缠"},
            {"event": "控制情绪", "desc": "容易因情绪波动影响关系"},
        ],
    },
    # 健康类
    "health": {
        "high": [
            {"event": "精力充沛", "desc": "体力状态极佳，适合运动锻炼"},
            {"event": "康复好转", "desc": "身体不适有好转迹象"},
            {"event": "心情愉悦", "desc": "精神状态好，做什么都顺心"},
            {"event": "免疫力增强", "desc": "身体抵抗力好，不易生病"},
        ],
        "medium": [
            {"event": "状态平稳", "desc": "注意作息规律即可"},
            {"event": "适合轻运动", "desc": "散步、瑜伽等轻度运动有益"},
            {"event": "饮食调理", "desc": "适合调整饮食结构"},
        ],
        "low": [
            {"event": "注意休息", "desc": "容易疲劳，避免熬夜"},
            {"event": "防范小病", "desc": "注意保暖，预防感冒"},
            {"event": "控制情绪", "desc": "容易焦虑，适合冥想放松"},
            {"event": "避免剧烈运动", "desc": "今天不适合高强度锻炼"},
        ],
    },
    # 出行类
    "travel": {
        "high": [
            {"event": "出行顺利", "desc": "旅途平安，可能有意外收获"},
            {"event": "贵人指路", "desc": "迷路或困难时有人帮忙"},
        ],
        "medium": [
            {"event": "出行平稳", "desc": "正常出行，无大碍"},
            {"event": "适合短途", "desc": "短途出行较顺利"},
        ],
        "low": [
            {"event": "谨慎出行", "desc": "出行可能遇到延误或阻碍"},
            {"event": "避免远行", "desc": "长途出行不太顺利"},
        ],
    },
    # 学业类
    "study": {
        "high": [
            {"event": "学习效率高", "desc": "理解力强，适合学习新知识"},
            {"event": "考试运佳", "desc": "考试或考核可能超常发挥"},
            {"event": "灵感迸发", "desc": "写作或创作有好灵感"},
        ],
        "medium": [
            {"event": "学习状态一般", "desc": "按计划学习即可"},
            {"event": "适合复习", "desc": "复习旧知识比学新知识效果好"},
        ],
        "low": [
            {"event": "注意力分散", "desc": "容易分心，需创造安静环境"},
            {"event": "避免临时抱佛脚", "desc": "突击学习效果不佳"},
        ],
    },
    # 社交类
    "social": {
        "high": [
            {"event": "人缘爆棚", "desc": "社交魅力强，容易获得好感"},
            {"event": "化解矛盾", "desc": "适合处理人际纠纷"},
            {"event": "拓展人脉", "desc": "可能认识有价值的新朋友"},
        ],
        "medium": [
            {"event": "社交平淡", "desc": "正常社交，无特别事件"},
            {"event": "适合独处", "desc": "今天适合自己待着"},
        ],
        "low": [
            {"event": "避免社交", "desc": "社交可能遇到不愉快"},
            {"event": "慎言慎行", "desc": "容易说错话得罪人"},
        ],
    },
}

# 幸运事件（基于喜用神）
LUCKY_EVENTS = {
    Wuxing.JIN: [
        {"event": "贵人相助", "desc": "可能得到权威人士的帮助", "icon": "👔"},
        {"event": "决断力强", "desc": "适合做重要决定", "icon": "⚡"},
    ],
    Wuxing.MU: [
        {"event": "创意迸发", "desc": "灵感涌现，适合创作", "icon": "💡"},
        {"event": "人际和谐", "desc": "与人相处融洽", "icon": "🤝"},
    ],
    Wuxing.SHUI: [
        {"event": "智慧闪光", "desc": "思维敏捷，学习效率高", "icon": "📚"},
        {"event": "财运暗涌", "desc": "可能有意外之财", "icon": "💎"},
    ],
    Wuxing.HUO: [
        {"event": "热情高涨", "desc": "社交活跃，魅力四射", "icon": "🔥"},
        {"event": "表现机会", "desc": "适合展示才华", "icon": "🌟"},
    ],
    Wuxing.TU: [
        {"event": "稳中求进", "desc": "踏实做事有回报", "icon": "🏔️"},
        {"event": "长辈助力", "desc": "可能得到长辈支持", "icon": "👴"},
    ],
}

# 图标映射
EVENT_ICONS = {
    "career": "💼",
    "wealth": "💰",
    "love": "💕",
    "health": "🏥",
}


def _judge_day_master_strength(bazi: dict) -> str:
    """判断日主强弱

    基于八字中五行数量分布，日主同五行+生我五行 > 我生+克我+我克 → 强。

    Returns:
        "strong" / "weak" / "balanced"
    """
    from fortune_engine.common.tiangan import Tiangan

    dm = Tiangan.from_name(bazi["day_master"])
    dm_wx = dm.wuxing
    five = bazi.get("five_elements") or {}
    if not five:
        return "balanced"

    # sheng(x) 返回 x 所生的五行（食伤方向）
    # 需要反向查表才能得到"谁生 x"（印方向）
    _BEI_SHENG = {v: k for k, v in SHENG_MAP.items()}  # 反向：被生 → 生者

    # 同类：比肩（同五行）+ 印（生我者）
    same_val = five.get(dm_wx.value, 0)
    yin_wx = _BEI_SHENG.get(dm_wx)  # 印的五行（谁生 dm_wx）
    yin_val = five.get(yin_wx.value, 0) if yin_wx else 0
    supportive = same_val + yin_val

    # 异类：食伤（我生）+ 财（我生之生）+ 官杀（克我者）
    food_god_wx = sheng(dm_wx)  # 我生 = 食伤
    wealth_wx = sheng(food_god_wx)  # 食伤生 = 财
    officer_wx = sheng(wealth_wx)  # 财生 = 官杀

    weakening = (
        five.get(food_god_wx.value, 0)
        + five.get(wealth_wx.value, 0)
        + five.get(officer_wx.value, 0)
    )

    if supportive >= weakening + 2:
        return "strong"
    elif weakening >= supportive + 2:
        return "weak"
    return "balanced"


def _parse_feedback_summary(feedback_summary: str) -> dict:
    """解析用户历史反馈摘要，提取各维度发生率"""
    import re
    result = {"total_rate": None, "dim_rates": {}}
    if not feedback_summary:
        return result

    # 提取总体发生率：如"发生率60%"
    m = re.search(r"发生率(\d+)%", feedback_summary)
    if m:
        result["total_rate"] = int(m.group(1)) / 100

    # 提取各维度发生率：如"career=70%"、"wealth=50%"
    for m in re.finditer(r"(\w+)=(\d+)%", feedback_summary):
        result["dim_rates"][m.group(1)] = int(m.group(2)) / 100

    return result


def _calculate_probability(
    score: int,
    daily_score: int,
    is_favorable: bool,
    ten_god: str,
    feedback_summary: str = "",
    dimension: str = "",
) -> int:
    """计算事件发生概率 (30-85%)

    融合日运评分(40%) + 时辰评分(60%)，叠加喜用神、十神、用户反馈修正。

    Args:
        score: 时辰运势评分 (1-5)
        daily_score: 每日运势评分 (1-5)
        is_favorable: 是否喜用神
        ten_god: 十神名称
        feedback_summary: 用户历史反馈摘要
        dimension: 事件维度（用于查反馈历史）
    """
    # 日运 40% + 时运 60% 的融合评分
    blended = daily_score * 0.4 + score * 0.6

    base = 30
    if blended >= 4.5:
        base += 35
    elif blended >= 3.5:
        base += 25
    elif blended >= 2.5:
        base += 15
    elif blended >= 1.5:
        base += 5

    # 喜用神加分
    if is_favorable:
        base += 10

    # 十神加分（区分吉凶程度）
    strong_positive = ["正印", "食神", "正财"]
    mild_positive = ["正官", "偏印"]
    mild_negative = ["伤官", "偏财"]
    strong_negative = ["劫财", "偏官"]

    if ten_god in strong_positive:
        base += 8
    elif ten_god in mild_positive:
        base += 5
    elif ten_god in mild_negative:
        base += 2
    elif ten_god in strong_negative:
        base -= 3

    # 用户历史反馈修正
    feedback = _parse_feedback_summary(feedback_summary)
    if feedback["dim_rates"] and dimension in feedback["dim_rates"]:
        dim_rate = feedback["dim_rates"][dimension]
        # 维度历史发生率高 → 微调 +5；低 → 微调 -5
        if dim_rate >= 0.6:
            base += 5
        elif dim_rate <= 0.3:
            base -= 5
    elif feedback["total_rate"] is not None:
        # 无维度数据时用总体发生率修正
        if feedback["total_rate"] >= 0.6:
            base += 3
        elif feedback["total_rate"] <= 0.3:
            base -= 3

    # 所有修正项叠加后理论最大值：30+35+10+8+5=88，clamp 到 85
    # 最小值：30-3-3=24，clamp 到 30
    return min(85, max(30, base))


def _get_best_hour_for_dimension(hourly: list, dimension: str) -> dict:
    """找到某个维度最吉利的时辰"""
    # 根据维度选择最佳时辰特征
    dimension_element_map = {
        "career": [Wuxing.JIN, Wuxing.TU],  # 金土利事业
        "wealth": [Wuxing.JIN, Wuxing.SHUI],  # 金水利财运
        "love": [Wuxing.MU, Wuxing.HUO],  # 木火利感情
        "health": [Wuxing.SHUI, Wuxing.MU],  # 水木利健康
    }

    target_elements = dimension_element_map.get(dimension, [])
    best_hour = None
    best_score = 0

    for h in hourly:
        element = h.get("element", "")
        score = h.get("score", 0)
        wx = Wuxing(element) if element in [e.value for e in Wuxing] else None

        if wx in target_elements and score > best_score:
            best_score = score
            best_hour = h

    if not best_hour:
        # 找评分最高的时辰
        best_hour = max(hourly, key=lambda x: x.get("score", 0))

    return best_hour


def generate_probability_events(
    bazi: dict,
    daily: dict,
    hourly: list,
    today: date,
    feedback_summary: str = "",
) -> list:
    """
    生成个性化概率事件（扩展版：8-12个事件）

    Args:
        bazi: 八字排盘结果
        daily: 今日运势
        hourly: 时辰运势列表
        today: 今日日期
        feedback_summary: 用户历史反馈摘要

    Returns:
        概率事件列表
    """
    events = []

    # 喜用神
    fav = set(bazi.get("favorable_elements", []))

    # 日主强弱判断（影响事件概率微调）
    dm_strength = _judge_day_master_strength(bazi)
    # 强日主：能承担更多，高概率事件+3；弱日主：宜保守，高概率事件-3
    strength_bias = {"strong": 3, "weak": -3, "balanced": 0}.get(dm_strength, 0)

    # 主维度评分
    main_dimensions = {
        "career": daily.get("career_fortune", {}).get("score", 3),
        "wealth": daily.get("wealth_fortune", {}).get("score", 3),
        "love": daily.get("love_fortune", {}).get("score", 3),
        "health": daily.get("health_fortune", {}).get("score", 3),
    }

    # 扩展维度（基于主维度+五行特征推算）
    overall_score = daily.get("overall_score", 3)
    dm_name = bazi.get("day_master", "")

    # 当日流日五行（用于扩展维度推算）
    from fortune_engine.common.tiangan import Tiangan
    flow_wx = None
    if daily.get("heavenly_stem"):
        try:
            flow_wx = Tiangan.from_name(daily["heavenly_stem"]).wuxing
        except Exception:
            pass

    # 出行：健康好+事业顺→出行佳，受克则不利
    travel_base = round((main_dimensions["health"] + main_dimensions["career"]) / 2)
    if flow_wx in [Wuxing.JIN, Wuxing.SHUI]:  # 金水流动性强，利出行
        travel_base = min(5, travel_base + 1)

    # 学业：日主为甲/壬（文昌星）加分，水木利学习
    study_base = overall_score
    if dm_name in ["甲", "壬", "癸"]:
        study_base = min(5, study_base + 1)
    if flow_wx in [Wuxing.SHUI, Wuxing.MU]:
        study_base = min(5, study_base + 1)

    # 社交：感情好→社交佳，火土利人际
    social_base = main_dimensions["love"]
    if flow_wx in [Wuxing.HUO, Wuxing.TU]:
        social_base = min(5, social_base + 1)

    extended_dimensions = {
        "travel": min(5, max(1, travel_base)),
        "study": min(5, max(1, study_base)),
        "social": min(5, max(1, social_base)),
    }

    all_dimensions = {**main_dimensions, **extended_dimensions}

    # 今日流日五行
    daily_element = None
    if hourly:
        import datetime
        current_hour = datetime.datetime.now().hour
        for h in hourly:
            if h.get("shichen_range", "").startswith(f"{current_hour:02d}") or \
               f"{current_hour:02d}" in h.get("shichen_range", ""):
                daily_element = h.get("element")
                break

    # 每个维度生成 1-2 个事件
    for dim, score in all_dimensions.items():
        # 找最佳时辰
        best_hour = _get_best_hour_for_dimension(hourly, dim)

        # 判断是否喜用神
        is_favorable = False
        if best_hour and best_hour.get("element"):
            is_favorable = best_hour["element"] in fav

        # 取该维度的日运评分
        dim_daily_score = main_dimensions.get(dim, overall_score)

        # 计算概率（融合日运+时运+反馈）
        probability = _calculate_probability(
            score=score,
            daily_score=dim_daily_score,
            is_favorable=is_favorable,
            ten_god=best_hour.get("ten_god", ""),
            feedback_summary=feedback_summary,
            dimension=dim,
        )

        # 日主强弱修正：强日主更敢做，弱日主宜保守
        probability = min(85, max(30, probability + strength_bias))

        # 选择事件模板
        templates = EVENT_TEMPLATES.get(dim, {})
        if probability >= 60:
            level = "high"
        elif probability >= 40:
            level = "medium"
        else:
            level = "low"

        template_list = templates.get(level, templates.get("medium", []))
        if not template_list:
            continue

        # 根据日期选择具体事件（确保同一天相同）
        # 使用 ord(dim[0]) 替代 hash(dim)，避免 PYTHONHASHSEED 导致不同进程结果不同
        day_seed = today.year * 10000 + today.month * 100 + today.day

        # 主维度生成 2 个事件，扩展维度生成 1 个
        count = 2 if dim in main_dimensions else 1
        for i in range(count):
            idx = (day_seed + ord(dim[0]) + i * 7) % len(template_list)
            selected = template_list[idx]

            # 时间范围
            time_range = "全天"
            if best_hour:
                time_range = best_hour.get("shichen_range", "全天")

            # 概率微调（同一维度不同事件概率略有差异）
            prob_adjust = i * 5 if i > 0 else 0
            final_prob = min(85, max(30, probability - prob_adjust))

            events.append({
                "dimension": dim,
                "icon": EVENT_ICONS.get(dim, "📌"),
                "event": selected["event"],
                "description": selected["desc"],
                "probability": final_prob,
                "time_range": time_range,
                "best_hour": best_hour.get("shichen", "") if best_hour else "",
                "element": best_hour.get("element", "") if best_hour else "",
                "ten_god": best_hour.get("ten_god", "") if best_hour else "",
                "is_favorable": is_favorable,
            })

    # 添加幸运事件（基于喜用神）
    if daily_element:
        wx = Wuxing(daily_element) if daily_element in [e.value for e in Wuxing] else None
        if wx and wx in LUCKY_EVENTS:
            lucky_list = LUCKY_EVENTS[wx]
            for i, lucky in enumerate(lucky_list):
                events.append({
                    "dimension": "lucky",
                    "icon": lucky.get("icon", "🍀"),
                    "event": lucky["event"],
                    "description": lucky["desc"],
                    "probability": 70 - i * 10,
                    "time_range": "全天",
                    "best_hour": "",
                    "element": daily_element,
                    "ten_god": "",
                    "is_favorable": True,
                })

    # 按概率排序
    events.sort(key=lambda x: x["probability"], reverse=True)

    return events
