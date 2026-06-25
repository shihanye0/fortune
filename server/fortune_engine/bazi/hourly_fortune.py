# -*- coding: utf-8 -*-
"""时辰运势推算：基于八字与流时干支的五行生克"""
from lunar_python import Solar
from fortune_engine.common.tiangan import Tiangan, TIANGAN_LIST
from fortune_engine.common.dizhi import Dizhi, DIZHI_LIST
from fortune_engine.common.wuxing import Wuxing, sheng, ke
from fortune_engine.common.shichen import SHICHEN_NAMES, hour_to_shichen


# 时辰运势描述模板（扩展版：每个十神 5-6 个事件）
HOURLY_EVENTS = {
    "比肩": {
        "events": [
            "与朋友相聚",
            "同行竞争出现",
            "合作机会来临",
            "志同道合的人出现",
            "团队项目有进展",
            "旧友重逢",
        ],
        "favorable": ["社交活动", "团队合作", "学习交流", "合伙经营", "信息共享"],
        "unfavorable": ["独自决策", "与人争执", "固执己见"],
    },
    "劫财": {
        "events": [
            "钱财有变动",
            "遇到竞争对手",
            "需要分享资源",
            "有人向你借钱",
            "合伙账目需理清",
            "意外支出出现",
        ],
        "favorable": ["谨慎理财", "低调行事", "审视合同", "控制开支"],
        "unfavorable": ["大额投资", "借贷担保", "冲动消费", "轻信他人"],
    },
    "正印": {
        "events": [
            "得到长辈帮助",
            "学习有收获",
            "贵人出现",
            "收到好消息",
            "考试或培训顺利",
            "领导给予指导",
        ],
        "favorable": ["学习进修", "寻求帮助", "签订合同", "读书充电", "接受指导"],
        "unfavorable": ["懒散懈怠", "拒绝帮助", "闭门造车"],
    },
    "偏印": {
        "events": [
            "灵感迸发",
            "遇到意外帮助",
            "思考深入",
            "发现新兴趣",
            "独处有收获",
            "直觉特别准",
        ],
        "favorable": ["研究创作", "独立思考", "艺术探索", "冥想静修"],
        "unfavorable": ["过度依赖他人", "钻牛角尖", "忽视现实"],
    },
    "食神": {
        "events": [
            "心情愉悦",
            "享受美食",
            "创意涌现",
            "社交场合受欢迎",
            "才艺展示机会",
            "收到礼物或请客",
        ],
        "favorable": ["社交娱乐", "艺术创作", "表达自我", "享受生活", "培养爱好"],
        "unfavorable": ["过度放纵", "贪图安逸", "忽视正事"],
    },
    "伤官": {
        "events": [
            "言语冲突",
            "想法特立独行",
            "挑战权威",
            "创意被看见",
            "与上级意见不合",
            "技术难题被攻克",
        ],
        "favorable": ["创新突破", "表达观点", "技术攻关", "独立项目"],
        "unfavorable": ["顶撞上司", "冲动发言", "口舌是非", "锋芒太露"],
    },
    "正官": {
        "events": [
            "获得认可",
            "责任加重",
            "遵守规则",
            "晋升考核",
            "接受新任务",
            "被委以重任",
        ],
        "favorable": ["汇报工作", "接受任务", "展现能力", "合规办事", "述职答辩"],
        "unfavorable": ["违规操作", "逃避责任", "敷衍了事"],
    },
    "偏官": {
        "events": [
            "压力增大",
            "遇到挑战",
            "需要决断",
            "竞争白热化",
            "突发事件需应对",
            "危机中藏机遇",
        ],
        "favorable": ["果断决策", "迎难而上", "锻炼意志", "突破瓶颈"],
        "unfavorable": ["逃避问题", "硬碰硬", "过度焦虑"],
    },
    "正财": {
        "events": [
            "收入稳定",
            "务实行动",
            "关注物质",
            "工资到账",
            "理财有收益",
            "报销款到账",
        ],
        "favorable": ["理财规划", "处理财务", "踏实工作", "储蓄计划", "账目整理"],
        "unfavorable": ["投机取巧", "贪小便宜", "忽视长期"],
    },
    "偏财": {
        "events": [
            "意外收获",
            "投资机会",
            "社交活跃",
            "中奖概率提升",
            "二手交易顺利",
            "兼职有进账",
        ],
        "favorable": ["投资理财", "拓展人脉", "把握机会", "适度冒险"],
        "unfavorable": ["贪心冒进", "赌博心态", "见利忘义"],
    },
}

# 五行时辰特质
# 农历月份 → 当令五行（月令旺衰）
# 春(寅卯辰)木旺, 夏(巳午未)火旺, 秋(申酉戌)金旺, 冬(亥子丑)水旺
# 辰戌丑未为四季土旺，但余气仍在
_SEASON_ELEMENT = {
    1: Wuxing.MU,    # 寅月 - 木旺
    2: Wuxing.MU,    # 卯月 - 木旺
    3: Wuxing.TU,    # 辰月 - 土旺（余气木）
    4: Wuxing.HUO,   # 巳月 - 火旺
    5: Wuxing.HUO,   # 午月 - 火旺
    6: Wuxing.TU,    # 未月 - 土旺（余气火）
    7: Wuxing.JIN,   # 申月 - 金旺
    8: Wuxing.JIN,   # 酉月 - 金旺
    9: Wuxing.TU,    # 戌月 - 土旺（余气金）
    10: Wuxing.SHUI,  # 亥月 - 水旺
    11: Wuxing.SHUI,  # 子月 - 水旺
    12: Wuxing.TU,    # 丑月 - 土旺（余气水）
}

# 辰戌丑未月的余气五行
_SEASON_REMAINING = {
    3: Wuxing.MU,    # 辰月余气 - 木
    6: Wuxing.HUO,   # 未月余气 - 火
    9: Wuxing.JIN,   # 戌月余气 - 金
    12: Wuxing.SHUI,  # 丑月余气 - 水
}


def _get_season_bonus(lunar_month: int, flow_wx: Wuxing) -> int:
    """月令旺衰修正：当令五行+1，余气五行+0（不扣分）

    Args:
        lunar_month: 农历月份 (1-12)
        flow_wx: 流时五行

    Returns:
        修正值 (0 或 1)
    """
    if lunar_month < 1 or lunar_month > 12:
        return 0

    # 当令五行得旺
    if _SEASON_ELEMENT.get(lunar_month) == flow_wx:
        return 1

    # 四季土月的余气也得力
    if lunar_month in _SEASON_REMAINING and _SEASON_REMAINING[lunar_month] == flow_wx:
        return 1

    return 0


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


def _score_from_hourly_relation(
    dm_wx: Wuxing,
    hour_stem_wx: Wuxing,
    hour_branch_wx: Wuxing,
    is_favorable: bool,
    ten_god: str = "",
) -> int:
    """根据日主与流时干支的五行关系打分 (1-5)

    综合天干五行(主)和地支五行(辅)的影响，同时区分十神吉凶。

    Args:
        dm_wx: 日主五行
        hour_stem_wx: 流时天干五行
        hour_branch_wx: 流时地支五行
        is_favorable: 流时五行是否为喜用神
        ten_god: 十神名称（用于区分同类五行的不同吉凶）
    """
    # 天干五行关系（主导，权重 70%）
    stem_base = 3
    if dm_wx == hour_stem_wx:
        stem_base = 3  # 比肩/劫财
    elif sheng(hour_stem_wx) == dm_wx:
        stem_base = 4  # 印（生我）
    elif sheng(dm_wx) == hour_stem_wx:
        stem_base = 3  # 食伤（我生）
    elif ke(hour_stem_wx) == dm_wx:
        stem_base = 2  # 官杀（克我）
    elif ke(dm_wx) == hour_stem_wx:
        stem_base = 4  # 财（我克）

    # 地支五行关系（辅助，权重 30%）
    branch_base = 3
    if dm_wx == hour_branch_wx:
        branch_base = 3
    elif sheng(hour_branch_wx) == dm_wx:
        branch_base = 4
    elif sheng(dm_wx) == hour_branch_wx:
        branch_base = 3
    elif ke(hour_branch_wx) == dm_wx:
        branch_base = 2
    elif ke(dm_wx) == hour_branch_wx:
        branch_base = 4

    # 加权融合（天干 70% + 地支 30%）
    raw = stem_base * 0.7 + branch_base * 0.3
    base = round(raw)

    # 十神微调已在 _calculate_probability 中按吉凶分档处理（+8/+5/+2/-3）
    # 此处不再重复扣分，保持评分层干净
    base = int(base)

    # 喜用神加分
    if is_favorable:
        base = min(5, base + 1)

    return max(1, min(5, base))


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

    # 4b. 流时地支五行
    flow_dz = Dizhi.from_name(hour_dz)
    flow_branch_wx = flow_dz.wuxing

    # 5. 是否喜用神
    fav = set(bazi.get("favorable_elements", []))
    is_favorable = flow_wx.value in fav

    # 7. 获取十神（先算十神，再用于评分微调）
    same_yinyang = dm.yinyang == flow_tg.yinyang
    ten_god = _get_ten_god_name(dm_wx, flow_wx, same_yinyang)

    # 6. 计算评分（融合天干+地支五行，含十神微调）
    score = _score_from_hourly_relation(dm_wx, flow_wx, flow_branch_wx, is_favorable, ten_god)

    # 6b. 月令旺衰修正：流时五行当令则+1
    lunar_month = lunar.getMonth()
    season_bonus = _get_season_bonus(lunar_month, flow_wx)
    score = max(1, min(5, score + season_bonus))

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
