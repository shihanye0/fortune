# -*- coding: utf-8 -*-
"""Spec 015: 用户反馈摘要服务

汇总用户历史反馈，生成摘要文本，用于 LLM prompt。
"""
from collections import Counter

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.daily_fortune import DailyFortune
from app.models.divination_record import DivinationRecord


def generate_feedback_summary(db: Session, user_id: int) -> str:
    """生成用户反馈摘要

    从 daily_fortunes 和 divination_records 中取最近 30 条有反馈的记录，
    汇总评分、标签、维度偏好，生成 200 字以内的摘要。
    """
    # 取最近有评分的每日运势
    fortune_rows = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.user_id == user_id,
            DailyFortune.user_rating.isnot(None),
        )
        .order_by(desc(DailyFortune.date))
        .limit(30)
        .all()
    )

    # 取最近有评分的占卜记录
    divination_rows = (
        db.query(DivinationRecord)
        .filter(
            DivinationRecord.user_id == user_id,
            DivinationRecord.user_rating.isnot(None),
        )
        .order_by(desc(DivinationRecord.created_at))
        .limit(30)
        .all()
    )

    # 无反馈时返回默认
    if not fortune_rows and not divination_rows:
        return "暂无用户反馈数据"

    parts = []

    # --- 每日运势反馈分析 ---
    if fortune_rows:
        ratings = [r.user_rating for r in fortune_rows]
        avg_rating = sum(ratings) / len(ratings)

        # 标签统计
        tag_counter: Counter = Counter()
        for row in fortune_rows:
            if row.user_feedback_tags:
                tag_counter.update(row.user_feedback_tags)

        # 维度偏好：从 feedback_text 中提取关键词
        dimension_counter: Counter = Counter()
        keywords_map = {
            "事业": "事业运",
            "工作": "事业运",
            "财运": "财运",
            "财富": "财运",
            "收入": "财运",
            "感情": "感情运",
            "爱情": "感情运",
            "恋爱": "感情运",
            "健康": "健康运",
            "身体": "健康运",
        }
        for row in fortune_rows:
            text = row.user_feedback_text or ""
            for kw, dim in keywords_map.items():
                if kw in text:
                    dimension_counter[dim] += 1

        lines = []
        lines.append(f"运势反馈({len(fortune_rows)}条):")
        lines.append(f"- 平均评分 {avg_rating:.1f}/5")

        if dimension_counter:
            top_dims = [d for d, _ in dimension_counter.most_common(2)]
            lines.append(f"- 更关注{'和'.join(top_dims)}")

        if tag_counter:
            top_tags = [t for t, _ in tag_counter.most_common(3)]
            lines.append(f"- 常见标签: {', '.join(top_tags)}")

        parts.append("\n".join(lines))

    # --- 占卜反馈分析 ---
    if divination_rows:
        ratings = [r.user_rating for r in divination_rows]
        avg_rating = sum(ratings) / len(ratings)
        parts.append(f"占卜反馈({len(divination_rows)}条): 平均评分 {avg_rating:.1f}/5")

    summary = "\n".join(parts)

    # 截断到 200 字
    if len(summary) > 200:
        summary = summary[:197] + "..."

    return summary
