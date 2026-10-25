# -*- coding: utf-8 -*-
"""冲煞推算与每日一卦：引擎口径 + 推送渲染测试。"""
from app.services.push_email import _build_html, _build_text
from app.services.push_feishu import _build_card
from fortune_engine.bazi.chongsha import get_day_chongsha
from fortune_engine.liuyao.hexagram import HEXAGRAM_MAP, HEXAGRAM_MEANING, daily_hexagram


class TestGetDayChongsha:
    """冲煞推算：以通行黄历口径为准。"""

    def test_known_almanac_values(self):
        """甲子冲马(戊午)煞南、壬申冲虎(丙寅)煞南、戊午冲鼠(壬子)煞北、乙丑冲羊(己未)煞东。"""
        assert get_day_chongsha("甲", "子") == {
            "clash_animal": "马", "clash_ganzhi": "戊午",
            "sha_direction": "南", "display": "冲马(戊午) 煞南", "display_short": "冲马 煞南",
        }
        assert get_day_chongsha("壬", "申")["display"] == "冲虎(丙寅) 煞南"
        assert get_day_chongsha("戊", "午")["display"] == "冲鼠(壬子) 煞北"
        assert get_day_chongsha("乙", "丑")["display"] == "冲羊(己未) 煞东"

    def test_clash_branch_is_six_apart(self):
        """任意日支：冲支恒为相隔六位。"""
        for dz in ("子", "寅", "辰", "午", "申", "戌", "丑", "卯", "巳", "未", "酉", "亥"):
            result = get_day_chongsha("甲", dz)
            assert result is not None

    def test_invalid_input_returns_none(self):
        """干支缺失或非法时返回 None 而非抛异常。"""
        assert get_day_chongsha(None, "子") is None
        assert get_day_chongsha("甲", None) is None
        assert get_day_chongsha("巳", "酉") is None  # 巳不是天干


class TestDailyHexagram:
    """每日一卦：确定性、覆盖度、个性化。"""

    def test_meaning_covers_all_64_hexagrams(self):
        """词表必须覆盖起卦可能出现的全部 64 卦名。"""
        assert set(HEXAGRAM_MAP.values()) == set(HEXAGRAM_MEANING.keys())

    def test_same_user_same_day_is_stable(self):
        a = daily_hexagram(42, 2026, 10, 25)
        b = daily_hexagram(42, 2026, 10, 25)
        assert a == b

    def test_different_users_get_different_hexagrams(self):
        results = {daily_hexagram(uid, 2026, 10, 25)["name"] for uid in range(12)}
        assert len(results) > 1

    def test_result_shape(self):
        result = daily_hexagram(42, 2026, 10, 25)
        assert result["name"] in HEXAGRAM_MEANING
        assert result["tendency"] in ("吉", "平", "慎")
        assert result["advice"]
        assert result["changing_lines"]
        assert result["changed_name"]


class TestExtrasRendering:
    """冲煞与今日一卦在邮件/飞书/纯文本三端的呈现。"""

    def _data(self) -> dict:
        return {
            "date": "2026-10-25",
            "day_ganzhi": "壬申",
            "day_chongsha": get_day_chongsha("壬", "申"),
            "daily_hexagram": daily_hexagram(42, 2026, 10, 25),
            "overall_score": 4,
            "interpretation": "解读文本",
        }

    def test_email_header_contains_chongsha(self):
        body = _build_html(self._data())
        assert "冲虎 煞南" in body

    def test_email_contains_hexagram_card(self):
        hexagram = daily_hexagram(42, 2026, 10, 25)
        body = _build_html(self._data())
        assert "今日一卦" in body
        assert hexagram["name"] in body
        assert hexagram["advice"] in body
        assert "变卦" in body

    def test_email_without_extras_renders_normally(self):
        """旧 payload 没有这两个字段时不报错、不出现对应模块。"""
        body = _build_html({"date": "2026-10-25", "overall_score": 3})
        assert "今日一卦" not in body
        assert "冲" not in body.split("DAILY FORTUNE BRIEF")[1][:200]

    def test_text_version_contains_extras(self):
        hexagram = daily_hexagram(42, 2026, 10, 25)
        text = _build_text(self._data())
        assert "冲煞：冲虎(丙寅) 煞南" in text
        assert f"今日一卦：{hexagram['name']}" in text

    def test_feishu_card_contains_extras(self):
        hexagram = daily_hexagram(42, 2026, 10, 25)
        card = _build_card(self._data())
        card_str = str(card)
        assert "壬申日" in card_str
        assert "冲虎 煞南" in card_str
        assert "今日一卦" in card_str
        assert hexagram["name"] in card_str
        assert "属虎" in card_str
