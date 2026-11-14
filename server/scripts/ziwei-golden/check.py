# -*- coding: utf-8 -*-
"""金标准比对：我们的 calculate_ziwei vs iztro 黄金用例（逐字段 diff）。"""
import json
import sys

sys.path.insert(0, "../..")
from fortune_engine.ziwei.chart import calculate_ziwei  # noqa: E402

FIXTURE = "../../tests/fixtures/ziwei_golden.json"


def diff_case(case):
    b = case["birth"]
    try:
        ours = calculate_ziwei(b["y"], b["m"], b["d"], b["h"], b["g"])
    except Exception as e:  # noqa: BLE001
        return [f"engine error: {e}"]
    ours = ours
    exp = case["expected"]
    diffs = []
    if ours["soul_palace"] != exp["soul"]:
        diffs.append("soul: %s != %s" % (ours["soul_palace"], exp["soul"]))
    if ours["body_palace"] != exp["body"]:
        diffs.append("body: %s != %s" % (ours["body_palace"], exp["body"]))
    for i in range(12):
        e = exp["palaces"][i]
        o = ours["palaces"][i]
        if o["name"] != e["name"]:
            diffs.append(f"palace{i} name {o['name']} != {e['name']}")
        if o["stem"] != e["stem"]:
            diffs.append(f"palace{i} stem {o['stem']} != {e['stem']}")
        for kind in ("major", "minor"):
            a = [(s["name"], s.get("brightness"), s.get("mutagen")) for s in o[kind + "_stars"]]
            b2 = [(s["n"], s["b"], s["m"]) for s in e[kind]]
            if a != b2:
                diffs.append(f"palace{i} {kind}: {a} != {b2}")
    e_dx = exp["da_xian"][i]
    o_dx = o.get("da_xian")
    if e_dx != (o_dx["start"], o_dx["end"]) if False else (tuple(e_dx) != (o_dx["start"], o_dx["end"])):
        diffs.append(f"palace{i} da_xian: {e_dx} != {o_dx['start']}..{o_dx['end']}")
    return diffs


if __name__ == "__main__":
    cases = json.load(open(FIXTURE, encoding="utf-8"))
    bad = 0
    for c in cases:
        ds = diff_case(c)
        if ds:
            bad += 1
            print("CASE", c["birth"], "->", ds[:6])
    print(f"PASS {len(cases) - bad}/{len(cases)}")
    sys.exit(1 if bad else 0)
