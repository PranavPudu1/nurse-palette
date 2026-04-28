"""Tiny helpers for generating + rendering sample schedules."""
from __future__ import annotations
import calendar
import random
from datetime import date
from typing import Dict, List

from theme import shift_chip, BORDER, GRID_HEADER, MUTED_FG, ACCENT, FG, CARD_BG

SHIFTS = ["D", "E", "N", "X"]
DAY_ABBR = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def make_pattern_schedule(nurses: List[str], year: int, month: int,
                          pattern: str = "balanced", seed: int = 0
                          ) -> Dict[str, List[str]]:
    """Generate a deterministic sample schedule for demoing / pairwise comparison."""
    rng = random.Random(seed)
    days = calendar.monthrange(year, month)[1]
    out: Dict[str, List[str]] = {}

    for ni, name in enumerate(nurses):
        row: List[str] = []
        for d in range(1, days + 1):
            dow = date(year, month, d).weekday()
            is_weekend = dow >= 5
            if pattern == "balanced":
                cycle = ["D", "D", "E", "X", "N", "N", "X"]
                shift = cycle[(d + ni) % len(cycle)]
                if is_weekend and rng.random() < 0.55:
                    shift = "X"
            elif pattern == "night-heavy":
                cycle = ["N", "N", "N", "X", "D", "E", "N", "X"]
                shift = cycle[(d + ni * 2) % len(cycle)]
            elif pattern == "block":
                kind = ["D", "E", "N"][ni % 3]
                shift = kind if (d + ni) % 7 < 4 else "X"
            else:
                shift = rng.choice(SHIFTS)
            row.append(shift)
        out[name] = row
    return out


def render_schedule_html(nurses: List[str], schedule: Dict[str, List[str]],
                         year: int, month: int, title: str | None = None,
                         badge: str | None = None) -> str:
    days = calendar.monthrange(year, month)[1]
    head_cell = (
        f"position:sticky;top:0;background:{GRID_HEADER};color:{MUTED_FG};"
        f"font-size:10px;font-weight:600;"
        f"border-bottom:1px solid {BORDER};padding:6px 2px;text-align:center;"
    )
    head_weekend = head_cell.replace(GRID_HEADER, ACCENT)
    name_cell = (
        f"position:sticky;left:0;background:{CARD_BG};color:{FG};"
        f"padding:6px 14px;font-size:13px;font-weight:500;"
        f"border-right:1px solid {BORDER};border-bottom:1px solid {BORDER};"
        f"white-space:nowrap;text-align:left;"
    )
    body_cell = (
        f"padding:2px 1px;text-align:center;color:{FG};"
        f"border-bottom:1px solid {BORDER};background:{CARD_BG};"
    )

    header_cells = []
    for d in range(1, days + 1):
        dow = date(year, month, d).weekday()
        style = head_weekend if dow >= 5 else head_cell
        header_cells.append(
            f'<th style="{style}min-width:32px;">'
            f'<div style="color:{MUTED_FG};">{DAY_ABBR[dow]}</div>'
            f'<div style="font-size:11px;color:{FG};font-weight:700;">{d}</div>'
            f'</th>'
        )

    body_rows = []
    for n in nurses:
        cells = "".join(
            f'<td style="{body_cell}">{shift_chip(s, 30)}</td>'
            for s in schedule[n]
        )
        body_rows.append(f'<tr><td style="{name_cell}">{n}</td>{cells}</tr>')

    title_html = ""
    if title or badge:
        badge_html = (
            f'<span class="np-pill" style="margin-left:8px;">{badge}</span>'
            if badge else ""
        )
        title_html = (
            f'<div style="font-weight:600;font-size:15px;color:{FG};margin-bottom:8px;'
            f'display:flex;align-items:center;">{title or ""}{badge_html}</div>'
        )

    return (
        f'<div>{title_html}'
        f'<div style="overflow:auto;border:1px solid {BORDER};border-radius:10px;'
        f'background:{CARD_BG};max-height:480px;">'
        f'<table style="border-collapse:collapse;width:100%;color:{FG};">'
        f'<thead><tr><th style="{head_cell}background:{GRID_HEADER};">Nurse</th>'
        f'{"".join(header_cells)}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table></div></div>'
    )


def render_single_calendar(year: int, month: int, shifts: List[str],
                           title: str | None = None, badge: str | None = None,
                           weekday_labels: List[str] | None = None) -> str:
    """Render one nurse's month as a calendar grid (Mon-first)."""
    days = calendar.monthrange(year, month)[1]
    labels = weekday_labels or DAY_ABBR
    first_dow = date(year, month, 1).weekday()

    weeks: list[list[tuple[int | None, str]]] = []
    cur: list[tuple[int | None, str]] = [(None, "")] * first_dow
    for d in range(1, days + 1):
        cur.append((d, shifts[d - 1] if d - 1 < len(shifts) else "X"))
        if len(cur) == 7:
            weeks.append(cur); cur = []
    if cur:
        while len(cur) < 7:
            cur.append((None, ""))
        weeks.append(cur)

    head = "".join(
        f'<th style="padding:8px;font-size:11px;color:{MUTED_FG};font-weight:600;'
        f'background:{GRID_HEADER};border-bottom:1px solid {BORDER};text-align:center;">'
        f'{lbl}</th>'
        for lbl in labels
    )
    rows = ""
    for w in weeks:
        cells = ""
        for i, (day_num, sh) in enumerate(w):
            is_weekend = i >= 5
            if day_num is None:
                cells += (
                    f'<td style="padding:8px;background:#F5F7FA;color:{MUTED_FG};'
                    f'border:1px solid {BORDER};height:62px;"></td>'
                )
            else:
                bg = ACCENT if is_weekend else CARD_BG
                cells += (
                    f'<td style="padding:6px;background:{bg};color:{FG};'
                    f'border:1px solid {BORDER};vertical-align:top;height:62px;">'
                    f'<div style="font-size:11px;color:{MUTED_FG};font-weight:500;'
                    f'margin-bottom:2px;">{day_num}</div>'
                    f'<div style="display:flex;justify-content:center;">'
                    f'{shift_chip(sh, 26)}</div></td>'
                )
        rows += f'<tr>{cells}</tr>'

    title_html = ""
    if title or badge:
        badge_html = (
            f'<span class="np-pill" style="margin-left:8px;">{badge}</span>'
            if badge else ""
        )
        title_html = (
            f'<div style="font-weight:600;font-size:15px;color:{FG};margin-bottom:8px;'
            f'display:flex;align-items:center;">{title or ""}{badge_html}</div>'
        )

    return (
        f'<div>{title_html}'
        f'<div style="border:1px solid {BORDER};border-radius:10px;overflow:hidden;'
        f'background:{CARD_BG};">'
        f'<table style="width:100%;border-collapse:collapse;color:{FG};">'
        f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div></div>'
    )


def schedule_summary(schedule: Dict[str, List[str]]) -> Dict[str, float]:
    total = sum(len(v) for v in schedule.values())
    counts = {s: 0 for s in SHIFTS}
    consec_nights = 0
    for row in schedule.values():
        for s in row:
            counts[s] += 1
        run = 0
        for s in row:
            if s == "N":
                run += 1
                if run >= 3:
                    consec_nights += 1
            else:
                run = 0
    return {
        "pct_off": counts["X"] / total * 100 if total else 0,
        "pct_night": counts["N"] / total * 100 if total else 0,
        "pct_day": counts["D"] / total * 100 if total else 0,
        "pct_evening": counts["E"] / total * 100 if total else 0,
        "long_night_runs": consec_nights,
    }
