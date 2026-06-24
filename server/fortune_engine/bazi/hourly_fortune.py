# -*- coding: utf-8 -*-
"""时辰运势推算：基于八字与流时干支的五行生克"""
from lunar_python import Solar
from fortune_engine.common.tiangan import Tiangan, TIANGAN_LIST
from fortune_engine.common.dizhi import Dizhi, DIZHI_LIST
from fortune_engine.common.wuxing import Wuxing, sheng, ke
from fortune_engine.common.shichen import SHICHEN_NAMES, hour_to_shichen


# 时辰运势描述模板
HOURLY_EVENTS = {
    "比肩": {
        "events": ["与朋友相聚", "同行竞争出现", "合作机会来临"],
        "favorable": ["社交活动", "团队合作", "学习交流"],
        "unfavorable": ["独自决策", "与人争执"],
    },
    "劫财": {
        "events": ["钱财有变动", "遇到竞争对手", "需要分享资源"],
        "favorable": ["谨慎理财", "低调行事"],
        "unfavorable": ["大额投资", "借贷担保"],
    },
    "正印": {
        "events": ["得到长辈帮助", "学习有收获", "贵人出现"],
        "favorable": ["学习进修", "寻求帮助", "签订合同"],
        "unfavorable": ["懒散懈怠"],
    },
    "偏印": {
        "events": ["灵感迸发", "遇到意外帮助", "思考深入"],
        "favorable": ["研究创作", "独立思考"],
        "unfavorable": ["过度依赖他人"],
    },
    "食神": {
        "events": ["心情愉悦", "享受美食", "创意涌现"],
        "favorable": ["社交娱乐", "艺术创作", "表达自我"],
        "unfavorable": ["过度放纵"],
    },
    "伤官": {
        "events": ["言语冲突", "想法特立独行", "挑战权威"],
        "favorable": ["创新突破", "表达观点"],
        "unfavorable": ["顶撞上司", "冲动发言"],
    },
    "正官": {
        "events": ["获得认可", "责任加重", "遵守规则"],
        "favorable": ["汇报工作", "接受任务", "展现能力"],
        "unfavorable": ["违规操作"],
    },
    "偏官": {
        "events": ["压力增大", "遇到挑战", "需要决断"],
        "favorable": ["果断决策", "迎难而上"],
        "unfavorable": ["逃避问题"],
    },
    "正财": {
        "events": ["收入稳定", "务实行动", "关注物质"],
        "favorable": ["理财规划", "处理财务", "踏实工作"],
        "unfavorable": ["投机取巧"],
    },
    "偏财": {
        "events": ["意外收获", "投资机会", "社交活跃"],
        "favorable": ["投资理财", "拓展人脉", "把握机会"],
        "unfavorable": ["贪心冒进"],
    },
}

# 五行时辰特质
WUXING_SHICHEN_TRAIT = {
    Wuxing.JIN: {"atmosphere": "肃杀果断", "energy": "收敛凝聚"},
    Wuxing.MU: {"atmosphere": "生机勃勃", "energy": "生长发散"},
    Wuxing.SHUI: {"atmosphere": "沉静内敛", "energy": "流动变化"},
    Wuxing.HUO: {"atmosphere": "热情活跃", "energy": "上升扩张"},
    Wuxing.TU: {"atmosphere": "稳重踏实", "energy": "承载包容"},
}


def _get_ten_god_name(dm_wx: Wuxing, other_wx: Wuxing, same_yinyang: bool) -> str:
    """获取十神名称"""
    if dm_wx == other_wx:
        return "比肩" if same_yinyang else "劫财"
    if sheng(other_wx) == dm_wx:
        return "偏印" if same_yinyang else "正印"
    if sheng(dm_wx) == other_wx:
        return "食神" if same_yinyang else "伤官"
    if ke(other_wx) == dm_wx:
        return "偏官" if same_yinyang else "正官"
    if ke(dm_wx) == other_wx:
        return "偏财" if same_yinyang else "正财"
    return "比肩"


def _score_from_hourly_relation(dm_wx: Wuxing, hour_wx: Wuxing, is_favorable: bool) -> int:
    """根据日主与流时天干的五行关系打分 (1-5)"""
    base = 3
    if dm_wx == hour_wx:
        base = 3  # 比肩
    elif sheng(hour_wx) == dm_wx:
        base = 4  # 印（生我）
    elif sheng(dm_wx) == hour_wx:
        base = 3  # 食伤（我生）
    elif ke(hour_wx) == dm_wx:
        base = 2  # 官杀（克我）
    elif ke(dm_wx) == hour_wx:
        base = 4  # 财（我克）

    # 喜用神加分
    if is_favorable:
        base = min(5, base + 1)
    return base


def calculate_hourly_fortune(
    bazi: dict,
    year: int,
    month: int,
    day: int,
    hour: int,
) -> dict:
    """
    推算时辰运势

    Args:
        bazi: 八字排盘结果
        year: 查询年
        month: 查询月
        day: 查询日
        hour: 查询时 (0-23)

    Returns:
        时辰运势字典
    """
    # 1. 获取时辰
    shichen_name = hour_to_shichen(hour)
    shichen_idx = SHICHEN_NAMES.index(shichen_name)

    # 2. 获取流时天干（日干 × 2 + 时辰地支序号，取天干）
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()
    day_tg = lunar.getDayGan()
    day_tg_idx = TIANGAN_LIST.index(Tiangan.from_name(day_tg))
    hour_tg_idx = (day_tg_idx * 2 + shichen_idx) % 10
    hour_tg = TIANGAN_LIST[hour_tg_idx].name
    hour_dz = shichen_name

    # 3. 日主信息
    dm = Tiangan.from_name(bazi["day_master"])
    dm_wx = dm.wuxing

    # 4. 流时天干五行
    flow_tg = Tiangan.from_name(hour_tg)
    flow_wx = flow_tg.wuxing

    # 5. 是否喜用神
    fav = set(bazi.get("favorable_elements", []))
    is_favorable = flow_wx.value in fav

    # 6. 计算评分
    score = _score_from_hourly_relation(dm_wx, flow_wx, is_favorable)

    # 7. 获取十神
    same_yinyang = dm.yinyang == flow_tg.yinyang
    ten_god = _get_ten_god_name(dm_wx, flow_wx, same_yinyang)

    # 8. 获取事件描述
    event_info = HOURLY_EVENTS.get(ten_god, HOURLY_EVENTS["比肩"])

    # 9. 时辰五行特质
    trait = WUXING_SHICHEN_TRAIT.get(flow_wx, {"atmosphere": "平和", "energy": "平稳"})

    return {
        "shichen": shichen_name,
        "shichen_range": f"{(shichen_idx * 2) % 24:02d}:00-{(shichen_idx * 2 + 2) % 24:02d}:00",
        "hourly_stem": hour_tg,
        "hourly_branch": hour_dz,
        "score": score,
        "ten_god": ten_god,
        "element": flow_wx.value,
        "atmosphere": trait["atmosphere"],
        "energy": trait["energy"],
        "events": event_info["events"],
        "favorable": event_info["favorable"],
        "unfavorable": event_info["unfavorable"],
    }


def calculate_all_hours_fortune(
    bazi: dict,
    year: int,
    month: int,
    day: int,
) -> list[dict]:
    """
    推算一天所有时辰的运势

    Returns:
        12 个时辰运势列表
    """
    results = []
    # 12 个时辰，每个时辰 2 小时
    for i in range(12):
        hour = (i * 2 + 1) % 24  # 取时辰中间的小时（如子时取 0 点）
        hourly = calculate_hourly_fortune(bazi, year, month, day, hour)
        results.append(hourly)
    return results
