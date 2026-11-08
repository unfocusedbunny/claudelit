"""
Claudelit robot #1: the GitHub issues collector.

Each run asks GitHub two questions about the Claude Code repo:
  1. How many new issues were opened each day?           (the "everyone" number)
  2. Which of them complain about quality in their title? (the "grumpy" number)
It saves the answers as CSV files in data/github/.

In plain words: it counts all new bug reports per day, and how many of them
say "it got worse". The grumpy share is our mood line.

Run:       python collectors/github_issues.py
Optional:  set GITHUB_TOKEN to go faster (GitHub Actions does this for you).
Days are counted in UTC, the way GitHub stores them.
"""
import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = "anthropics/claude-code"
START = date(2026, 9, 22)  # Opus 5.5 launch day
OUT = Path(__file__).resolve().parent.parent / "data" / "github"
RECHECK_DAYS = 3  # re-count the latest days, since GitHub's search can lag a little

# The complaint dictionary: an issue counts as a complaint if its TITLE has one
# of these. GitHub allows at most 5 ORs per search, so the words come in groups
# (one search per group). Edit freely, then re-run.
COMPLAINT_GROUPS = [
    ["degraded", "degradation", "degrades", "nerfed", "dumber", '"got worse"'],
    ['"quality regression"', '"low quality"', '"poor quality"', '"output quality"', '"getting worse"'],
]
# Left out on purpose: "lazy" (mostly matched "lazy-load" feature requests).
OPUS_55 = re.compile(r"opus[\s-]*5[.\-]5|5\.5[\s-]*opus", re.I)


def search(query, page=1, per_page=100):
    """Ask GitHub's issue search one question and return its answer."""
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "per_page": per_page, "page": page})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "claudelit"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    while True:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
                result = json.load(r)
            time.sleep(2.5)  # stay under GitHub's search speed limit
            return result
        except urllib.error.HTTPError as e:
            # Speed limit hit: wait as long as GitHub says, then try again.
            if e.headers.get("Retry-After"):
                time.sleep(int(e.headers["Retry-After"]) + 1)
            elif e.headers.get("X-RateLimit-Remaining") == "0":
                time.sleep(max(int(e.headers["X-RateLimit-Reset"]) - time.time(), 0) + 2)
            else:
                raise


def count_new_issues(day):
    return search(f"repo:{REPO} is:issue created:{day}", per_page=1)["total_count"]


def find_complaints(start, end):
    found = {}
    for words in COMPLAINT_GROUPS:
        query = f"repo:{REPO} is:issue in:title created:{start}..{end} ({' OR '.join(words)})"
        page = 1
        while True:
            result = search(query, page=page)
            if result["total_count"] > 1000 or result["incomplete_results"]:
                print("WARNING: GitHub returned a partial list for:", query)
            for item in result["items"]:
                found[item["number"]] = item
            if len(result["items"]) < 100 or page * 100 >= 1000:
                break
            page += 1
    return found


def matched_words(title):
    title = title.lower().replace("-", " ")
    words = [w.strip('"') for group in COMPLAINT_GROUPS for w in group if w.strip('"') in title]
    return words or ["(near match)"]  # GitHub matched the words, but not side by side


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)  # finished days only
    daily_path = OUT / "daily.csv"

    # 1. The "everyone" number: reuse days we already counted, ask only for new ones.
    totals = {}
    if daily_path.exists():
        with open(daily_path, newline="") as f:
            totals = {row["date"]: int(row["new_issues"]) for row in csv.DictReader(f)}
    for n in range((yesterday - START).days + 1):
        day = START + timedelta(days=n)
        if day.isoformat() not in totals or day > yesterday - timedelta(days=RECHECK_DAYS):
            totals[day.isoformat()] = count_new_issues(day)
            print(day, totals[day.isoformat()], "new issues")

    # 2. The "grumpy" number: every complaint issue since launch, saved one per row.
    complaints = sorted(find_complaints(START, yesterday).values(), key=lambda i: i["created_at"])
    with open(OUT / "complaint_issues.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "number", "title", "url", "matched_words", "mentions_opus_5_5", "state"])
        for i in complaints:
            w.writerow([i["created_at"][:10], i["number"], i["title"], i["html_url"],
                        "; ".join(matched_words(i["title"])),
                        bool(OPUS_55.search(i["title"] + " " + (i["body"] or ""))), i["state"]])

    # 3. One row per day, ready for the chart.
    per_day = Counter(i["created_at"][:10] for i in complaints)
    per_day_opus = Counter(i["created_at"][:10] for i in complaints
                           if OPUS_55.search(i["title"] + " " + (i["body"] or "")))
    with open(daily_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "new_issues", "complaint_issues", "complaint_share_pct",
                    "complaints_mentioning_opus_5_5"])
        for d in sorted(totals):
            share = round(100 * per_day[d] / totals[d], 2) if totals[d] else ""
            w.writerow([d, totals[d], per_day[d], share, per_day_opus[d]])

    print(f"Done: {len(complaints)} complaint issues across {len(totals)} days.")


if __name__ == "__main__":
    main()
