"""Business Hours / Maintenance Window Engine.

Lets the user declare, per entity (or globally), when a system is
expected to be open/active - and computes, at any instant: is it open
right now, and if not, exactly how long until the next open window and
how long that window lasts. Detections that fall inside a declared
maintenance window are suppressed (with the window recorded as evidence,
never silently dropped).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


@dataclass
class OpenStatus:
    is_open: bool
    current_window: tuple[str, str] | None
    next_open_at: datetime | None
    seconds_until_next_open: float | None
    next_window_duration_seconds: float | None


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(hour=int(h), minute=int(m))


def _windows_for_day(schedule: dict, day_key: str) -> list[tuple[time, time]]:
    raw = schedule.get(day_key, [])
    out = []
    for start, end in raw:
        out.append((_parse_hhmm(start), _parse_hhmm(end)))
    return out


def evaluate_schedule(schedule: dict, now: datetime | None = None) -> OpenStatus:
    """`schedule` example:
    {"mon": [["09:00","18:00"]], "tue": [["09:00","18:00"]], ..., "sat": [], "sun": []}
    An empty list for a day means closed all day. A missing key is
    treated the same as an empty list (closed).
    """
    now = now or datetime.now(timezone.utc)

    # Check current day first.
    today_key = DAY_KEYS[now.weekday()]
    for start, end in _windows_for_day(schedule, today_key):
        start_dt = now.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
        end_dt = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if start_dt <= now <= end_dt:
            return OpenStatus(
                is_open=True,
                current_window=(start.strftime("%H:%M"), end.strftime("%H:%M")),
                next_open_at=None,
                seconds_until_next_open=None,
                next_window_duration_seconds=None,
            )

    # Not open now — scan forward up to 8 days to find the next window.
    for offset in range(0, 8):
        day = now + timedelta(days=offset)
        day_key = DAY_KEYS[day.weekday()]
        for start, end in _windows_for_day(schedule, day_key):
            candidate_start = day.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
            candidate_end = day.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
            if candidate_start <= now and offset == 0:
                continue  # window already passed today
            if candidate_start > now:
                duration = (candidate_end - candidate_start).total_seconds()
                return OpenStatus(
                    is_open=False,
                    current_window=None,
                    next_open_at=candidate_start,
                    seconds_until_next_open=(candidate_start - now).total_seconds(),
                    next_window_duration_seconds=duration,
                )

    return OpenStatus(
        is_open=False,
        current_window=None,
        next_open_at=None,
        seconds_until_next_open=None,
        next_window_duration_seconds=None,
    )


def is_within_maintenance(windows: list[dict], now: datetime | None = None) -> bool:
    """`windows` is a list of BusinessHours rows flagged is_maintenance_window=True.
    Returns True if `now` falls inside any of them."""
    now = now or datetime.now(timezone.utc)
    for w in windows:
        status = evaluate_schedule(w.get("schedule", {}), now)
        if status.is_open:
            return True
    return False
