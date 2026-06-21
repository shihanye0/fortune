# -*- coding: utf-8 -*-
"""Spec 015: 用户反馈摘要服务

汇总用户历史反馈，生成摘要文本，用于 LLM prompt。
"""
from collections import Counter

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.daily_fortune import DailyFortune
from app.models.divination_record import DivinationRecord
from app.models.prediction_outcome import PredictionOutcome


# 维度关键词映射
_KEYWORDS_MAP = {
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


def _extract_dimension_counter(rows) -> Counter:
    """从反馈文本中提取维度偏好计数"""
    counter: Counter = Counter()
    for row in rows:
        text = row.user_feedback_text or ""
        for kw, dim in _KEYWORDS_MAP.items():
            if kw in text:
                counter[dim] += 1
    return counter


def get_accuracy_info(db: Session, user_id: int) -> str:
    """获取用户历史准确率信息

    从 daily_fortunes 和 divination_records 的 accuracy_mark 字段统计，
    返回如 "运势准确率: 75% (12/16), 占卜准确率: 80% (8/10)" 的文本。
    """
    parts = []

    # 每日运势准确率
    fortune_marks = (
        db.query(DailyFortune.accuracy_mark)
        .filter(
            DailyFortune.user_id == user_id,
            DailyFortune.accuracy_mark.isnot(None),
        )
        .all()
    )
    if fortune_marks:
        total = len(fortune_marks)
        accurate = sum(1 for m in fortune_marks if m[0] == 1)
        pct = int(accurate * 100 / total)
        parts.append(f"运势准确率: {pct}% ({accurate}/{total})")

    # 占卜准确率
    div_marks = (
        db.query(DivinationRecord.accuracy_mark)
        .filter(
            DivinationRecord.user_id == user_id,
            DivinationRecord.accuracy_mark.isnot(None),
        )
        .all()
    )
    if div_marks:
        total = len(div_marks)
        accurate = sum(1 for m in div_marks if m[0] == 1)
        pct = int(accurate * 100 / total)
        parts.append(f"占卜准确率: {pct}% ({accurate}/{total})")

    return "; ".join(parts) if parts else ""


def get_dimension_preference(db: Session, user_id: int) -> str:
    """获取用户维度偏好文本

    从最近有反馈的每日运势中统计维度关注倾向，
    返回如 "更关注事业运和财运" 的文本。
    """
    rows = (
        db.query(DailyFortune)
        .filter(
            DailyFortune.user_id == user_id,
            DailyFortune.user_feedback_text.isnot(None),
        )
        .order_by(desc(DailyFortune.date))
        .limit(30)
        .all()
    )
    if not rows:
        return ""

    counter = _extract_dimension_counter(rows)
    if not counter:
        return ""

    top_dims = [d for d, _ in counter.most_common(2)]
    return f"更关注{'和'.join(top_dims)}"


def get_outcome_history(db: Session, user_id: int) -> str:
    """获取预测验证结果历史

    从 prediction_outcomes 表查询 verified=True 的记录，
    返回最近验证结果的摘要文本。
    """
    outcomes = (
        db.query(PredictionOutcome)
        .filter(
            PredictionOutcome.user_id == user_id,
            PredictionOutcome.verified.isnot(None),
        )
        .order_by(desc(PredictionOutcome.verified_at))
        .limit(10)
        .all()
    )
    if not outcomes:
        return ""

    total = len(outcomes)
    confirmed = sum(1 for o in outcomes if o.verified)
    denied = total - confirmed

    parts = [f"已验证{total}条预测: {confirmed}条确认发生, {denied}条未发生"]

    # 列出最近几条验证结果文本
    recent_texts = []
    for o in outcomes[:3]:
        if o.outcome_text:
            status = "确认" if o.verified else "未发生"
            recent_texts.append(f"[{status}] {o.outcome_text[:50]}")
    if recent_texts:
        parts.append("最近验证: " + "; ".join(recent_texts))

    return "\n".join(parts)


def generate_feedback_summary(db: Session, user_id: int) -> str:
    """生成用户反馈摘要

    从 daily_fortunes、divination_records 和 prediction_outcomes 中取最近记录，
    汇总评分、标签、维度偏好、准确率、验证结果，生成 300 字以内的摘要。
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

    # 查询已验证的预测结果
    outcome_rows = (
        db.query(PredictionOutcome)
        .filter(
            PredictionOutcome.user_id == user_id,
            PredictionOutcome.verified.isnot(None),
        )
        .order_by(desc(PredictionOutcome.verified_at))
        .limit(10)
        .all()
    )

    # 无反馈时返回默认
    if not fortune_rows and not divination_rows and not outcome_rows:
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

        # 维度偏好
        dimension_counter = _extract_dimension_counter(fortune_rows)

        # 准确率统计
        accuracy_marks = [r.accuracy_mark for r in fortune_rows if r.accuracy_mark is not None]
        accuracy_line = ""
        if accuracy_marks:
            accurate_count = sum(1 for m in accuracy_marks if m == 1)
            pct = int(accurate_count * 100 / len(accuracy_marks))
            accuracy_line = f"- 准确率 {pct}% ({accurate_count}/{len(accuracy_marks)})"

        lines = []
        lines.append(f"运势反馈({len(fortune_rows)}条):")
        lines.append(f"- 平均评分 {avg_rating:.1f}/5")

        if accuracy_line:
            lines.append(accuracy_line)

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

        # 占卜准确率
        accuracy_marks = [r.accuracy_mark for r in divination_rows if r.accuracy_mark is not None]
        acc_text = ""
        if accuracy_marks:
            accurate_count = sum(1 for m in accuracy_marks if m == 1)
            pct = int(accurate_count * 100 / len(accuracy_marks))
            acc_text = f", 准确率 {pct}%"

        parts.append(f"占卜反馈({len(divination_rows)}条): 平均评分 {avg_rating:.1f}/5{acc_text}")

    # --- 预测验证结果 ---
    if outcome_rows:
        total = len(outcome_rows)
        confirmed = sum(1 for o in outcome_rows if o.verified)
        parts.append(f"预测验证({total}条): {confirmed}条确认, {total - confirmed}条未确认")

    summary = "\n".join(parts)

    # 截断到 300 字
    if len(summary) > 300:
        summary = summary[:297] + "..."

    return summary
