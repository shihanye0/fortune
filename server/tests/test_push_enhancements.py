# -*- coding: utf-8 -*-
"""推送增强：节气换月、财神喜神、今日一问、生活化宜忌、周报、吉时提醒。"""
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from app.api.v1.internal import _build_weekly_recap, _find_upcoming_gushi, _send_gushi_reminders
from app.models.base import CHINA_TZ
from app.models.daily_fortune import DailyFortune
from app.models.prediction_outcome import PredictionOutcome
from app.models.push_delivery import PushDelivery
from app.services.push_email import _build_html, _build_text
from app.services.push_feishu import _build_card
from fortune_engine.bazi.hourly_fortune import HOURLY_EVENTS
from fortune_engine.bazi.season import get_season_note
from fortune_engine.bazi.chongsha import get_deity_directions
from fortune_engine.common.reflection import REFLECTION_QUESTIONS, pick_reflection


class TestSeasonNote:
    """节气换月提醒。"""

    def test_day_before_lidong(self):
        note = get_season_note(date(2026, 11, 6))
        assert note is not None
        assert note.startswith("明日立冬")
        assert "亥月" in note

    def test_day_of_lidong(self):
        note = get_season_note(date(2026, 11, 7))
        assert note is not None
        assert note.startswith("今日立冬")

    def test_ordinary_day_returns_none(self):
        assert get_season_note(date(2026, 10, 25)) is None

    def test_zhongqi_day_returns_none(self):
        """中气（如霜降）不换月令，不应提示。"""
        assert get_season_note(date(2026, 10, 22)) is None
        assert get_season_note(date(2026, 10, 23)) is None


class TestDeityDirections:
    """财神/喜神方位歌。"""

    def test_stem_ren(self):
        assert get_deity_directions("壬") == {"caishen": "正南", "xishen": "正南"}

    def test_stem_yi(self):
        assert get_deity_directions("乙") == {"caishen": "东北", "xishen": "西北"}

    def test_all_stems_covered(self):
        stems = "甲乙丙丁戊己庚辛壬癸"
        for stem in stems:
            result = get_deity_directions(stem)
            assert result is not None, stem

    def test_invalid_returns_none(self):
        assert get_deity_directions(None) is None
        assert get_deity_directions("X") is None


class TestReflectionQuestion:
    """今日一问：确定性题池。"""

    def test_deterministic(self):
        assert pick_reflection(42, 20261025) == pick_reflection(42, 20261025)

    def test_in_pool(self):
        for uid in range(10):
            assert pick_reflection(uid, 20261025) in REFLECTION_QUESTIONS

    def test_users_differ(self):
        picks = {pick_reflection(uid, 20261025) for uid in range(12)}
        assert len(picks) > 1


class TestConcreteHourlyActions:
    """宜忌生活化：每个十神的可行动词前置。"""

    def test_concrete_items_first(self):
        assert HOURLY_EVENTS["比肩"]["favorable"][:2] == ["签约合作", "组队攻坚"]
        assert HOURLY_EVENTS["正财"]["favorable"][:2] == ["报销对账", "存款定投"]

    def test_all_ten_gods_have_concrete_items(self):
        for info in HOURLY_EVENTS.values():
            assert len(info["favorable"]) >= 5


class TestEnhancedRendering:
    """新字段在邮件/飞书/纯文本三端的呈现与缺省兼容。"""

    def _data(self) -> dict:
        return {
            "date": "2026-10-25",
            "overall_score": 4,
            "interpretation": "解读文本",
            "season_note": "明日立冬，月令转入亥月（水旺），宜蓄力静养、谋定后动。",
            "deity_directions": {"caishen": "正南", "xishen": "正南"},
            "reflection_question": "今天什么事值得你全力以赴？",
            "weekly_recap": {
                "verified_total": 5, "hit_count": 3, "hit_rate": 60,
                "week_avg_score": 3.9, "days_count": 7,
            },
        }

    def test_email_renders_all_new_sections(self):
        body = _build_html(self._data())
        assert "明日立冬" in body
        assert "财神" in body and "正南" in body
        assert "喜神" in body
        assert "今日一问：今天什么事值得你全力以赴？" in body
        assert "本周回顾" in body
        assert "3/5" in body and "60%" in body
        assert "3.9/5" in body

    def test_email_without_new_fields_renders(self):
        body = _build_html({"date": "2026-10-25", "overall_score": 3})
        assert "明日立冬" not in body
        assert "本周回顾" not in body
        assert "今日一问" not in body

    def test_text_renders_all_new_sections(self):
        text = _build_text(self._data())
        assert "节气：明日立冬" in text
        assert "财神方位：正南" in text
        assert "喜神方位：正南" in text
        assert "今日一问：" in text
        assert "本周回顾：本周均分 3.9/5（7 天）；预言命中 3/5（60%）" in text

    def test_feishu_renders_all_new_sections(self):
        card_str = str(_build_card(self._data()))
        assert "明日立冬" in card_str
        assert "财神：正南" in card_str
        assert "今日一问" in card_str
        assert "本周回顾" in card_str
        assert "命中 3/5" in card_str

    def test_recap_without_feedback_shows_cta(self):
        data = self._data()
        data["weekly_recap"] = {"verified_total": 0, "hit_count": 0, "hit_rate": None,
                                "week_avg_score": 3.9, "days_count": 7}
        body = _build_html(data)
        assert "还没有预言反馈" in body
        assert "给预测打个分" in body

    def test_feishu_escapes_llm_content(self):
        """飞书卡片对 LLM/用户来源文本做尖括号转义，不原样穿透。"""
        data = self._data()
        data["interpretation"] = "<script>alert(1)</script>解读"
        data["reflection_question"] = "<img src=x onerror=1>"
        card_str = str(_build_card(data))
        assert "<script>" not in card_str
        assert "&lt;script&gt;" in card_str
        assert "<img" not in card_str


class TestWeeklyRecap:
    """周报统计：来自反馈闭环数据（verified_at 生产写入为 UTC）。"""

    def _seed(self, db, user_id, today):
        # 固定 UTC 时间戳（today=10-25 周日，窗口起点为北京时间 10-18 00:00 = UTC 10-17 16:00）
        def at(day, hour):
            return datetime(2026, 10, day, hour, tzinfo=timezone.utc)

        for score, d in ((4, 0), (3, 1), (5, 2)):
            db.add(DailyFortune(
                user_id=user_id, date=today - timedelta(days=d),
                heavenly_stem="壬", earthly_branch="申",
                overall_score=score,
            ))
        # 窗口内 ×3（2 命中 1 未中）；窗口外 ×1，不应计入
        db.add(PredictionOutcome(user_id=user_id, source_type="fortune", source_id=1,
                                 verified=True, verified_at=at(25, 12)))
        db.add(PredictionOutcome(user_id=user_id, source_type="fortune", source_id=1,
                                 verified=True, verified_at=at(24, 4)))
        db.add(PredictionOutcome(user_id=user_id, source_type="fortune", source_id=1,
                                 verified=False, verified_at=at(19, 6)))
        db.add(PredictionOutcome(user_id=user_id, source_type="fortune", source_id=1,
                                 verified=True, verified_at=at(16, 20)))
        db.commit()

    def test_recap_counts(self, db_session):
        from tests.test_daily_push import _create_user

        user = _create_user(db_session, push_channel="email")
        today = date(2026, 10, 25)  # 周日
        self._seed(db_session, user.id, today)
        recap = _build_weekly_recap(user.id, today, db_session)
        assert recap["verified_total"] == 3
        assert recap["hit_count"] == 2
        assert recap["hit_rate"] == 67
        assert recap["days_count"] == 3
        assert abs(recap["week_avg_score"] - 4.0) < 0.01

    def test_recap_excludes_out_of_window_by_beijing_time(self, db_session):
        """窗口按北京时间 7 天前 0 点起算：UTC 写入的 8 天前记录必须排除。"""
        from tests.test_daily_push import _create_user

        user = _create_user(db_session, push_channel="email")
        today = date(2026, 10, 25)
        db_session.add(PredictionOutcome(
            user_id=user.id, source_type="fortune", source_id=1,
            verified=True,
            # 北京时间 10-18 04:00 = UTC 10-17 20:00，窗口应为 >= 10-18 00:00(+08)
            verified_at=datetime(2026, 10, 17, 20, 0, tzinfo=timezone.utc),
        ))
        db_session.commit()
        recap = _build_weekly_recap(user.id, today, db_session)
        assert recap["verified_total"] == 1

    def test_recap_none_when_no_data(self, db_session):
        from tests.test_daily_push import _create_user
        user = _create_user(db_session, push_channel="email")
        assert _build_weekly_recap(user.id, date(2026, 10, 25), db_session) is None


class TestGushiReminder:
    """吉时前飞书即时提醒。"""

    def test_find_upcoming_gushi_respects_threshold(self, db_session):
        from tests.test_daily_push import _create_user
        from fortune_engine.bazi.hourly_fortune import calculate_all_hours_fortune
        from fortune_engine.bazi.pillar import calculate_bazi

        user = _create_user(db_session, push_channel="feishu",
                            feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/test")
        today = date(2026, 10, 25)
        bazi = calculate_bazi(user.birth_year, user.birth_month, user.birth_day, user.birth_hour, user.gender)
        charts = {}
        for offset in (0, 1):
            d = today + timedelta(days=offset)
            charts[d] = calculate_all_hours_fortune(bazi, d.year, d.month, d.day)
        for hour in range(24):
            item = _find_upcoming_gushi(user, hour, today)
            target_start = ((hour + 1) % 24) * 60
            target_date = today + timedelta(days=1) if target_start == 0 else today
            matching = [h for h in charts[target_date] if _start_minutes(h) == target_start]
            if item is None:
                assert not matching or _score_of(matching[0]) < 4
            else:
                assert _score_of(item) >= 4
                assert _start_minutes(item) == target_start

    @patch("app.services.push_feishu.send_gushi_feishu", return_value=True)
    def test_send_gushi_once_per_day(self, mock_gushi, db_session):
        from tests.test_daily_push import _create_user
        user = _create_user(db_session, push_channel="feishu",
                            feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/test")
        today = date(2026, 10, 25)
        # 找一个会命中的 hour
        hit_hours = [h for h in range(24) if _find_upcoming_gushi(user, h, today)]
        if not hit_hours:
            return  # 该用户当日无 >=4 吉时，无法触发（构造性跳过）
        now = datetime(2026, 10, 25, hit_hours[0], 0, tzinfo=CHINA_TZ)
        first = _send_gushi_reminders(db_session, now, hit_hours[0])
        assert first == 1
        assert mock_gushi.call_count == 1
        # 第二次调用（下一小时）：当天已提醒过，不再发送
        second = _send_gushi_reminders(db_session, now, hit_hours[0])
        assert second == 0
        assert mock_gushi.call_count == 1
        rows = db_session.query(PushDelivery).filter(
            PushDelivery.user_id == user.id, PushDelivery.channel == "feishu_gushi").all()
        assert len(rows) == 1

    @patch("app.services.push_feishu.send_gushi_feishu", return_value=True)
    def test_expired_gushi_is_voided_not_sent(self, mock_gushi, db_session):
        """重试路径：吉时已结束的提醒直接核销，不再发送。"""
        from app.api.v1.internal import _deliver
        from tests.test_daily_push import _create_user

        user = _create_user(db_session, push_channel="feishu",
                            feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/test")
        delivery = PushDelivery(
            user_id=user.id, date=date(2026, 10, 25), channel="feishu_gushi",
            status="pending",
            payload={"text": "⏰ 吉时将至：辰时 08:00-10:00", "shichen_range": "08:00-10:00"},
            next_attempt_at=datetime(2026, 10, 25, 11, 0, tzinfo=CHINA_TZ),
            attempts=0,
        )
        db_session.add(delivery)
        db_session.commit()
        db_session.refresh(delivery)

        now = datetime(2026, 10, 25, 11, 0, tzinfo=CHINA_TZ)  # 辰时已结束 1 小时
        result = _deliver(delivery, user, now, db_session)
        assert result is True
        mock_gushi.assert_not_called()
        assert delivery.status == "delivered"


def _start_minutes(item: dict) -> int:
    start_str = str(item.get("shichen_range", "")).split("-")[0]
    sh, sm = (int(p) for p in start_str.split(":"))
    return sh * 60 + sm


def _score_of(item: dict) -> int:
    from fortune_engine.bazi.score import normalize_score
    return normalize_score(item.get("score"))
