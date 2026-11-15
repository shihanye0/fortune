# -*- coding: utf-8 -*-
"""Local push preview generator (temp tool)."""
import sys
sys.path.insert(0, '.')
from datetime import datetime, timedelta, timezone
from fortune_engine.ziwei.chart import calculate_ziwei
from fortune_engine.ziwei.words import daily_signal
from app.services.push_email import _build_html, _build_text

CH = timezone(timedelta(hours=8))
now = datetime(2026, 11, 15, 7, 5, tzinfo=CH)
chart = calculate_ziwei(1990, 8, 15, 7, 0)

hours = []
for i in range(12):
    names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    ranges = ["23:00-01:00", "01:00-03:00", "03:00-05:00", "05:00-07:00", "07:00-09:00",
              "09:00-11:00", "11:00-13:00", "13:00-15:00", "15:00-17:00", "17:00-19:00",
              "19:00-21:00", "21:00-23:00"]
    stems = ["庚", "辛", "壬", "癸", "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛"]
    scores = [3, 2, 3, 5, 4, 3, 2, 4, 3, 2, 3, 4]
    favorable = {"卯": ["启动新事", "签约"], "未": ["推进重点任务"], "亥": ["复盘"]}
    favorable = favorable.get(names[i], ["规划"])
    ten_gods = ["正财", "偏财", "七杀", "正印", "正官", "七杀", "正印", "偏印", "正官", "偏官", "正印", "偏印"]
    hours.append({"shichen": names[i], "shichen_range": ranges[i], "score": scores[i],
                  "favorable": favorable, "unfavorable": ["休息"] if scores[i] <= 2 else [],
                  "hourly_stem": stems[i], "hourly_branch": names[i],
                  "ten_god": ten_gods[i], "element": "水", "events": []})

payload = {
    "date": "2026-11-15", "day_ganzhi": "丁亥日",
    "day_chongsha": {"display": "蛇日冲猪(乙亥)煞西", "display_short": "冲猪煞西"},
    "overall_score": 4,
    "career": {"score": 4, "detail": "适合推进协作类任务"},
    "wealth": {"score": 3, "detail": "细水长流，忌冲动消费"},
    "love": {"score": 4, "detail": "宜坦诚沟通"},
    "health": {"score": 3, "detail": "注意作息"},
    "lucky_color": "靛蓝", "lucky_number": "6",
    "lucky_direction": "东南",
    "deity_directions": {"caishen": "正西", "xishen": "西北"},
    "season_note": "后天立冬后首个节气：小雪（2天后）",
    "interpretation": "今日整体偏顺，事业维度打开，宜推进协作；忌在情绪上头时做决定。",
    "hourly_fortunes": hours,
    "probability_events": [
        {"dimension": "事业", "event": "推进重点任务", "probability": 82, "best_hour": "未",
         "time_range": "13:00-15:00", "description": "流时十神得地，协作动作阻力最小"},
        {"dimension": "人际", "event": "回复旧消息", "probability": 55, "best_hour": "卯",
         "time_range": "05:00-07:00", "description": "旧关系修复窗口，早间回复更显诚意"},
        {"dimension": "幸运", "event": "穿幸运色", "probability": 70, "time_range": "全天",
         "description": "幸运色与日干相生，顺势加分"},
    ],
    "daily_hexagram": {"name": "水火既济", "tendency": "吉", "advice": "事将成之际最忌松懈",
                       "changed_name": "水火未济", "upper_trigram": "坎", "lower_trigram": "离"},
    "hexagram_interpretation": "既济卦：事情将成之际最忌松懈。今天推进到 80% 的任务最值得收尾，上午贵人现身时敲定关键细节。",
    "ziwei_daily": {
        "soul_palace": "卯", "five_elements": "土五局", "sihua": daily_signal(chart, 3),
        "daxian": {"range_text": "35-44岁", "palace_display": "子女宫", "hint": "子女缘分与创作成果"},
        "flow_ganzhi": "丙午",
        "flow_sihua": daily_signal(chart, 2),
        "interpretation": "今日化忌落夫妻宫，亲密关系上少说教、多倾听；化禄落迁移宫，外出办事与远行沟通格外顺，可主动推进。",
    },
    "bazi_dayun": {"pillar": "甲申", "start_year": 2023, "end_year": 2032, "start_age": 34, "end_age": 43},
    "daily_overview": {"interpretation": "今日主基调偏顺：日运 4/5，一卦「水火既济」主事将成，紫微化禄落迁移宫利外出推进。最值得做的是把卡了 80% 的任务收尾、主动约谈合作。最需留意的是化忌落夫妻宫，亲密关系上少说教多倾听，别把工作情绪带回家。"},
    "reflection_question": "今天最想推进一步的那件事，卡住你的到底是什么？",
    "calculation_notice": "传统文化参考，不构成医疗、法律或投资建议。",
}
html = _build_html(payload, now=now)
open('E:/fortune/docs/preview/push-preview-2026-11-15.html', 'w', encoding='utf-8').write(html)
text = _build_text(payload, now=now)

open('E:/fortune/docs/preview/push-preview-text.txt', 'w', encoding='utf-8').write(text)
print('HTML', len(html), 'TEXT', len(text))
