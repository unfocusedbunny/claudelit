"""
Claudelit robot #2: the LiveNerf collector.

LiveNerf (github.com/ninjahawk/livenerf, MIT licence) asks Opus 5.5 the same 78
tricky questions every day, plus 12 to Opus 5 as a control, and publishes the
daily scores in one file. This robot copies that file into data/livenerf/.

In plain words: someone else does the testing, we keep a copy of their notebook.

Run:  python collectors/livenerf.py
"""
import csv
import io
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/ninjahawk/livenerf/main/results/daily.csv"
OUT = Path(__file__).resolve().parent.parent / "data" / "livenerf" / "daily.csv"
NEEDED = {"date_utc", "model", "arm", "family", "samples", "scored", "score"}


def main():
    with urllib.request.urlopen(urllib.request.Request(SOURCE, headers={"User-Agent": "claudelit"})) as r:
        text = r.read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    missing = NEEDED - set(rows[0]) if rows else NEEDED
    if missing:  # LiveNerf changed its format: stop rather than save something the page can't read
        raise SystemExit(f"LiveNerf file is missing columns {sorted(missing)}, nothing saved.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    days = sorted({row["date_utc"] for row in rows})
    print(f"Saved {len(rows)} rows, {days[0]} to {days[-1]}.")


if __name__ == "__main__":
    main()
