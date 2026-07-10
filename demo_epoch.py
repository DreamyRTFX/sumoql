"""
demo_epoch.py — Demo of a Discord epoch-timestamp helper.

Discord renders <t:UNIX:STYLE> as a live, per-viewer-localized timestamp.
No timezone guessing, no hardcoded "8PM EST" that's wrong for everyone else.

Styles:
  t  short time        3:00 PM
  T  long time         3:00:00 PM
  d  short date        07/12/2026
  D  long date         July 12, 2026
  f  short date/time   July 12, 2026 3:00 PM      (default)
  F  long date/time    Sunday, July 12, 2026 3:00 PM
  R  relative          in 2 days / 3 hours ago
"""

from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))


def discord_ts(dt: datetime, style: str = "f") -> str:
    """Return a Discord timestamp tag for a datetime.

    Naive datetimes are assumed to be JST (the tournament's home timezone).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return f"<t:{int(dt.timestamp())}:{style}>"


if __name__ == "__main__":
    # Day 1 of Nagoya 2026 — 2nd Sunday, bouts open ~9AM JST
    day1 = datetime(2026, 7, 12, 9, 0, tzinfo=JST)

    print("Raw datetime:", day1, "\n")
    print("All styles for Day 1 opening:")
    for style in ("t", "T", "d", "D", "f", "F", "R"):
        print(f"  :{style:<1}  ->  {discord_ts(day1, style)}")

    print("\nHow you'd drop it into a briefing line:")
    print(f"  The Nagoya Basho begins {discord_ts(day1, 'R')}.")
    print(f"  First bout: {discord_ts(day1, 'F')}")

    print("\nDaily card — replaces the hardcoded '8PM EST' string:")
    day3 = day1 + timedelta(days=2)  # Day 3
    print(f"  DAY 3 CARD — bouts begin {discord_ts(day3, 'R')} ({discord_ts(day3, 'f')})")

    print("\nRaw tags (what actually goes in the payload):")
    print(f"  {discord_ts(day1, 'R')}  {discord_ts(day1, 'F')}")
