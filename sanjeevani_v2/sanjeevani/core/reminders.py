"""Real medicine reminders: schedules the next 24 hours of doses on the
patient's phone through ntfy, so it rings at medicine time even when
the website is closed."""
import time
from datetime import datetime, timedelta, timezone

from core import meds, notify

IST = timezone(timedelta(hours=5, minutes=30))
SLOT_HOURS = {"Morning (8 AM)": 8, "Afternoon (2 PM)": 14, "Night (9 PM)": 21}


def next_times(now=None):
    """Each slot's next occurrence in India time (today if still ahead, else tomorrow)."""
    now = now or datetime.now(IST)
    out = {}
    for slot, hour in SLOT_HOURS.items():
        when = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if when <= now + timedelta(minutes=1):
            when += timedelta(days=1)
        out[slot] = when
    return out


def schedule_day(med_list, name, body_for):
    """body_for(slot, meds_text) -> message text. Returns list of (slot, datetime)."""
    done = []
    for slot, when in sorted(next_times().items(), key=lambda x: x[1]):
        items = meds.schedule(med_list)[slot]
        if not items:
            continue
        text = body_for(slot, ", ".join(m["brand"] for m in items))
        notify.ntfy_send(f"Medicine time - {name}", text, priority="high", tags="pill,alarm_clock",
                         at=when.timestamp(), topic=notify.reminder_topic())
        done.append((slot, when))
    return done


def test_reminder(name, text, seconds=60):
    notify.ntfy_send(f"Medicine time - {name}", text, priority="high", tags="pill,alarm_clock",
                     at=time.time() + seconds, topic=notify.reminder_topic())
