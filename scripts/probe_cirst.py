import httpx
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from icalendar import Calendar

url = "https://framagenda.org/remote.php/dav/public-calendars/zQHSGsKNDxPwAFr6?export"
cal = Calendar.from_ical(httpx.get(url, timeout=60).content)
montreal = ZoneInfo("America/Montreal")
dates = []
for comp in cal.walk():
    if comp.name != "VEVENT":
        continue
    dt = comp.get("dtstart").dt
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time(), tzinfo=montreal)
    elif isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=montreal)
    dates.append(dt)
print("total events", len(dates))
print("max date", max(dates) if dates else None)
print("2026 events", sum(1 for d in dates if d.year == 2026))
for d in sorted(d for d in dates if d.year >= 2025)[-10:]:
    print(d.date())
