# -*- coding: utf-8 -*-
"""True solar time (NOAA equation-of-time approximation).

Ported from Renhuai123/ziwei-doushu lib/ziwei/true-solar-time.ts (MIT).
Conventions: local true solar time = clock time + longitude correction
+ equation of time; longitude correction = (longitude - meridian) * 4 min;
meridian = 120 deg for UTC+8. Valid range 1900-2026.
"""
import math
from datetime import date, timedelta

MINUTES_PER_DAY = 1440
SECONDS_PER_DAY = 86400


def _mod(v, base):
    return (v % base + base) % base


def is_valid_gregorian_date(y, m, d):
    try:
        date(y, m, d)
        return True
    except (ValueError, TypeError):
        return False


def day_of_year(y, m, d):
    return (date(y, m, d) - date(y, 1, 1)).days + 1


def equation_of_time_minutes(y, m, d, clock_hour=12, clock_minute=0):
    """NOAA equation of time, minutes; positive = solar ahead of mean time."""
    if not is_valid_gregorian_date(y, m, d):
        return 0.0
    days_in_year = 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365
    fractional_hour = clock_hour + clock_minute / 60
    gamma = (2 * math.pi / days_in_year) * (day_of_year(y, m, d) - 1 + (fractional_hour - 12) / 24)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def calculate_true_solar_time(y, m, d, clock_hour, clock_minute, longitude):
    """Clock time + longitude correction + EOT. Returns dict; day_offset for date shift."""
    meridian = 120
    lon_corr = (longitude - meridian) * 4 if longitude is not None else 0.0
    eot = equation_of_time_minutes(y, m, d, clock_hour, clock_minute) if longitude is not None else 0.0
    total = lon_corr + eot
    raw_minutes = clock_hour * 60 + clock_minute + total
    rounded_seconds = round(raw_minutes * 60)
    day_offset = math.floor(rounded_seconds / SECONDS_PER_DAY)
    second_of_day = _mod(rounded_seconds, SECONDS_PER_DAY)
    hour = second_of_day // 3600
    minute = (second_of_day % 3600) // 60
    normalized_minutes = second_of_day / 60
    if normalized_minutes >= 1380 or normalized_minutes < 60:
        branch = 0
    else:
        branch = int((normalized_minutes - 60) // 120) + 1
    return {
        "hour": hour, "minute": minute, "day_offset": day_offset,
        "branch": branch,
        "longitude_correction": lon_corr, "eot": eot,
        "total_correction": total,
        "clock": f"{hour:02d}:{minute:02d}",
    }


def adjusted_birth_for_chart(y, m, d, hour, longitude):
    """Ziwei chart input adapter: returns (y2, m2, d2, shichen, note) or None.

    longitude None -> no correction (standard clock time). Cross-day shift
    moves the lunar date used by the chart (day_offset applied).
    """
    if longitude is None:
        return None
    r = calculate_true_solar_time(y, m, d, int(hour), 0, float(longitude))
    nd = date(y, m, d) + timedelta(days=r["day_offset"])
    shichen = r["branch"] if r["branch"] != 0 or r["clock"] >= "23" else 0
    note = (
        f"已按真太阳时校正：经度 {longitude}°（修正 {r['longitude_correction']:+.0f} 分钟），"
        f"均时差 {r['eot']:+.1f} 分钟，钟表 {hour:02d}:00 → 真太阳时 {r['clock']}"
    )
    return nd.year, nd.month, nd.day, r["branch"], note
