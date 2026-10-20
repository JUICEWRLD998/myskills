#!/usr/bin/env python
"""Deterministic checker for baked market-holiday tables (US/NYSE observance rules).

Validated 2026-09 on Fables' SessionLib.bakedClosed (2026-2030 tables) — found exactly one
real defect: New Year's Day 2028 (Sat 2028-01-01) is observed Fri 2027-12-31, and that row was
missing from both the 2027 and 2028 tables (2028 had 9 rows; every other year 10).

Usage:
    python verify_baked_calendar.py            # runs the built-in Fables 2026-2030 tables
    python verify_baked_calendar.py tables.json  # tables.json = {"2026": [101,119,...], ...}
                                                  # (mmdd ints per year)

Rules checked (NYSE):
  - every baked date must fall Mon-Fri;
  - fixed holidays (NYD 1/1, Juneteenth 6/19, Independence 7/4, Christmas 12/25):
    Sat -> observed prior Friday, Sun -> observed following Monday;
  - floating: MLK 3rd Mon Jan, Presidents 3rd Mon Feb, Good Friday (Easter - 2d),
    Memorial last Mon May, Labor 1st Mon Sep, Thanksgiving 4th Thu Nov.
Output: per-year MISSING/EXTRA lines; exit 0 = tables match ground truth, 1 = issues found.
"""
import datetime
import json
import sys

# Fables SessionLib.bakedClosed 2026-2030 (the validated default; replace with your target's)
DEFAULT_TABLES = {
    2026: [101, 119, 216, 403, 525, 619, 703, 907, 1126, 1225],
    2027: [101, 118, 215, 326, 531, 618, 705, 906, 1125, 1224],
    2028: [117, 221, 414, 529, 619, 704, 904, 1123, 1225],
    2029: [101, 115, 219, 330, 528, 619, 704, 903, 1122, 1225],
    2030: [101, 121, 218, 419, 527, 619, 704, 902, 1128, 1225],
}
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def nth_weekday(y, m, weekday, n):
    c = 0
    for d in range(1, 32):
        try:
            if datetime.date(y, m, d).weekday() == weekday:
                c += 1
                if c == n:
                    return datetime.date(y, m, d)
        except ValueError:
            break


def last_weekday(y, m, weekday):
    for d in range(31, 0, -1):
        try:
            if datetime.date(y, m, d).weekday() == weekday:
                return datetime.date(y, m, d)
        except ValueError:
            continue


def easter(y):
    # Anonymous Gregorian algorithm
    a, b, c = y % 19, y // 100, y % 100
    d = (19 * a + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
    d += (7 - (y + y // 4 + d - b // 4 + 2) % 7) % 7
    if d == 29:
        d = 28
    if d == 28 and a > 10:
        d = 27
    return datetime.date(y, 3, 22) + datetime.timedelta(days=d - 1)


def observed(y, m, d):
    """NYSE-observed closure date for a fixed holiday (Sat->Fri before, Sun->Mon after)."""
    wd = datetime.date(y, m, d).weekday()
    if wd == 5:
        return datetime.date(y, m, d) - datetime.timedelta(days=1)
    if wd == 6:
        return datetime.date(y, m, d) + datetime.timedelta(days=1)
    return datetime.date(y, m, d)


def ground_truth(y):
    """Set of (y, m, d) closures NYSE observes in calendar year y (prior-year NYD observance
    is reported under its own year so the checker can match it against the prior table)."""
    out = set()
    for name, (m, d) in {"NYD": (1, 1), "Juneteenth": (6, 19), "Indep": (7, 4), "Christmas": (12, 25)}.items():
        obs = observed(y, m, d)
        out.add((obs.year, obs.month, obs.day))  # may be y-1 (NYD Sat) or y+1 (Dec25 Sat is never y+1)
    for nm, dt in {
        "MLK": nth_weekday(y, 1, 0, 3),
        "Presidents": nth_weekday(y, 2, 0, 3),
        "GoodFriday": easter(y) - datetime.timedelta(days=2),
        "Memorial": last_weekday(y, 5, 0),
        "Labor": nth_weekday(y, 9, 0, 1),
        "Thanksgiving": nth_weekday(y, 11, 3, 4),
    }.items():
        out.add((dt.year, dt.month, dt.day))
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        tables = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}
    else:
        tables = DEFAULT_TABLES
    issues = 0
    for y in sorted(tables):
        baked = {(y, mmdd // 100, mmdd % 100) for mmdd in tables[y]}
        for (yy, m, d) in sorted(baked):
            if datetime.date(yy, m, d).weekday() >= 5:
                print(f"{y}: baked date {yy}-{m:02d}-{d:02d} falls on a WEEKEND")
                issues += 1
        truth = ground_truth(y)
        for (yy, m, d) in sorted(truth - baked):
            if yy == y:
                print(f"{y}: MISSING closure {yy}-{m:02d}-{d:02d} ({DOW[datetime.date(yy, m, d).weekday()]})")
                issues += 1
            elif yy < y:
                # prior-year observance (e.g. NYD 2028 -> Fri 2027-12-31): must live in the PRIOR table
                prior = tables.get(y - 1, [])
                if (yy, m, d) not in {(y - 1, mm // 100, mm % 100) for mm in prior}:
                    print(f"{y}: NYD-type observance {yy}-{m:02d}-{d:02d} MISSING from year {y - 1} table")
                    issues += 1
        for (yy, m, d) in sorted(baked - truth):
            print(f"{y}: EXTRA closure {yy}-{m:02d}-{d:02d} (not a known NYSE holiday)")
            issues += 1
    print(f"scan complete; issues: {issues}")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
