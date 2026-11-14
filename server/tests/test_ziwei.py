# -*- coding: utf-8 -*-
"""紫微斗数引擎测试：金标准 diff（54 例）+ 词表完整性 + 时辰折算 + DST + 确定性。"""
import json
import os

import pytest

from fortune_engine.ziwei.chart import (
    BRIGHTNESS, SI_HUA_TABLE, calculate_ziwei, clock_hour_to_shichen,
)
from fortune_engine.common.dst_cn import is_china_dst, XLS_CN
from fortune_engine.ziwei.words import PALACE_MEANINGS, SIHUA_MEANINGS, STAR_TRAITS

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "ziwei_golden.json")


def _goldens():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def test_golden_cases():
    """54 个金标准用例逐字段 diff（与 iztro 逐字段一致）。"""
    for case in _goldens():
        b = case["birth"]
        exp = case["expected"]
        ours = calculate_ziwei(b["y"], b["m"], b["d"], b["h"], b["g"])
        msg = f"case={b}"
        assert ours["soul_palace"] == exp["soul"], msg
        assert ours["body_palace"] == exp["body"], msg
        assert ours["five_elements"] == exp["five_elements"], msg
        assert ours["ming_zhu"] == exp["ming_zhu"], msg
        assert ours["shen_zhu"] == exp["shen_zhu"], msg
        for i in range(12):
            e, o = exp["palaces"][i], ours["palaces"][i]
            assert o["name"] == e["name"], (msg, i, "name")
            assert o["stem"] == e["stem"], (msg, i, "stem")
            for kind in ("major", "minor"):
                ea = [(s["n"], s["b"], s["m"]) for s in e[kind]]
                oa = [(s["name"], s.get("brightness"), s.get("mutagen")) for s in o[kind + "_stars"]]
                assert oa == ea, (msg, i, kind)
        e_dx = tuple(exp["da_xian"][i])
        o_dx = o.get("da_xian")
        assert (o_dx["start"], o_dx["end"]) == e_dx, (msg, i, "da_xian")


def test_shichen_mapping():
    assert clock_hour_to_shichen(0) == 0
    assert clock_hour_to_shichen(1) == 1
    assert clock_hour_to_shichen(2) == 1
    assert clock_hour_to_shichen(7) == 4
    assert clock_hour_to_shichen(23) == 0
    assert clock_hour_to_shichen(22) == 11


def test_hour_gender_validation():
    for bad_hour in (-1, 24, 2.5):
        with pytest.raises(ValueError):
            calculate_ziwei(1990, 8, 15, bad_hour, 1)
    for bad_gender in (-1, 2, "m"):
        with pytest.raises(ValueError):
            calculate_ziwei(1990, 8, 15, 10, bad_gender)


def test_determinism():
    a = calculate_ziwei(1990, 8, 15, 7, 0)
    b2 = calculate_ziwei(1990, 8, 15, 7, 0)
    a.pop("flow_year", None)
    b2.pop("flow_year", None)
    assert a == b2


def test_dst_boundaries():
    assert is_china_dst(1987, 4, 11) is False
    assert is_china_dst(1987, 4, 12) is True
    assert is_china_dst(1987, 9, 13) is True
    assert is_china_dst(1987, 9, 14) is False
    assert is_china_dst(1986, 5, 4) is True
    assert is_china_dst(1986, 5, 3) is False
    assert len(XLS_CN) == 36
    for row in XLS_CN:
        assert len(row) == 5


def test_words_completeness():
    assert len(STAR_TRAITS) == 14
    assert len(PALACE_MEANINGS) == 12
    assert len(SIHUA_MEANINGS) == 4
    assert len(BRIGHTNESS) == 20
    assert len(SI_HUA_TABLE) == 10
    for star, row in BRIGHTNESS.items():
        assert len(row) == 12
