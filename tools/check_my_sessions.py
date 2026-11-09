"""
Claudelit session checker: was I in a Claude Code experiment?

Reads the Claude Code session files on YOUR computer and prints, for each
experiment ID it finds, how Opus 5.5 behaved for you:
  - how often a reply used 2 or more tools
  - how long its Bash commands were
  - how long its visible answers and its thinking were
  - which effort level was on

Nothing is sent anywhere. It reads numbers and IDs only, never your prompts or code.

Run:   python3 check_my_sessions.py
Also:  python3 check_my_sessions.py --by week        (group by week instead of experiment)
       python3 check_my_sessions.py --csv summary.csv  (save the table, numbers only)
       python3 check_my_sessions.py --dir PATH         (if your sessions live somewhere else)

How it works: Claude Code saves each session as a .jsonl file in ~/.claude/projects/.
Lines of type "atis-latch" record the experiment ID that was active (empty = none).
Every reply after that line counts toward that ID until the next one.
"""
import argparse
import csv
import json
import os
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

NO_ID = "none"
NOT_RECORDED = "not recorded"  # older sessions, from before Claude Code wrote these lines


def default_dir():
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(base) / "projects" if base else Path.home() / ".claude" / "projects"


def read_replies(files, model):
    """One entry per API reply on the main thread, de-duplicated across files."""
    replies, seen_blocks = {}, set()
    for path in files:
        atis = NOT_RECORDED
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(o, dict):
                    continue
                if o.get("type") == "atis-latch":
                    atis = o.get("atis") or NO_ID
                    continue
                if o.get("type") != "assistant" or o.get("isSidechain"):
                    continue  # only the main conversation, not subagents
                msg = o.get("message") or {}
                rid = o.get("requestId")
                if not rid or model not in (msg.get("model") or ""):
                    continue
                block = (rid, o.get("apiBlockIndex", o.get("uuid")))
                if block in seen_blocks:  # resumed sessions repeat earlier lines
                    continue
                seen_blocks.add(block)
                r = replies.setdefault(rid, {
                    "id": atis, "day": (o.get("timestamp") or "")[:10], "effort": o.get("effort") or "unknown",
                    "tools": 0, "bash": [], "output": 0, "thinking": 0})
                for c in msg.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        r["tools"] += 1
                        if c.get("name") == "Bash":
                            r["bash"].append(len(str((c.get("input") or {}).get("command", ""))))
                usage = msg.get("usage") or {}
                r["output"] = max(r["output"], usage.get("output_tokens") or 0)
                r["thinking"] = max(r["thinking"], (usage.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
    return list(replies.values())


def week_of(day):
    try:
        y, w, _ = date.fromisoformat(day).isocalendar()
        return f"{y}-W{w:02d}"
    except ValueError:
        return "unknown"


def summarise(replies, by):
    groups = defaultdict(list)
    for r in replies:
        groups[r["id"] if by == "id" else week_of(r["day"])].append(r)
    med = lambda xs: round(statistics.median(xs)) if xs else ""
    rows = []
    for key, rs in groups.items():
        days = sorted(r["day"] for r in rs if r["day"])
        efforts = Counter(r["effort"] for r in rs)
        rows.append({
            "group": key,
            "from": days[0] if days else "",
            "to": days[-1] if days else "",
            "replies": len(rs),
            "pct_2plus_tools": round(100 * sum(r["tools"] >= 2 for r in rs) / len(rs)),
            "median_bash_chars": med([n for r in rs for n in r["bash"]]),
            "median_visible_tokens": med([max(r["output"] - r["thinking"], 0) for r in rs]),
            "median_thinking_tokens": med([r["thinking"] for r in rs]),
            "effort": ", ".join(f"{e} {round(100 * n / len(rs))}%" for e, n in efforts.most_common()),
        })
    return sorted(rows, key=lambda row: (row["from"], row["group"]))


def print_table(rows, by):
    cols = [("group", "experiment" if by == "id" else "week"), ("from", "from"), ("to", "to"), ("replies", "replies"),
            ("pct_2plus_tools", "2+ tools %"), ("median_bash_chars", "bash chars"),
            ("median_visible_tokens", "answer tokens"), ("median_thinking_tokens", "thinking tokens"), ("effort", "effort")]
    table = [[label for _, label in cols]] + [[str(row[k]) for k, _ in cols] for row in rows]
    widths = [max(len(line[i]) for line in table) for i in range(len(cols))]
    for n, line in enumerate(table):
        print("  ".join(cell.ljust(w) for cell, w in zip(line, widths)))
        if n == 0:
            print("  ".join("-" * w for w in widths))


def main():
    p = argparse.ArgumentParser(description="Check your own Claude Code sessions for experiments. Nothing is sent anywhere.")
    p.add_argument("--dir", type=Path, default=default_dir(), help="folder with your session files (default: ~/.claude/projects)")
    p.add_argument("--model", default="opus-5-5", help="only count replies from models whose name contains this (default: opus-5-5)")
    p.add_argument("--by", choices=["id", "week"], default="id", help="group by experiment ID (default) or by week")
    p.add_argument("--csv", type=Path, help="also save the table as a CSV file (numbers only)")
    args = p.parse_args()

    files = sorted(args.dir.glob("*/*.jsonl"))
    if not files:
        raise SystemExit(f"No session files found in {args.dir}. Use --dir to point at your Claude Code projects folder.")
    replies = read_replies(files, args.model)
    print(f"Read {len(files)} session files on this computer: {len(replies)} {args.model} replies on the main thread.")
    print("Nothing was sent anywhere.\n")
    if not replies:
        return
    rows = summarise(replies, args.by)
    print_table(rows, args.by)
    print("\n'none' means no experiment was active. 'not recorded' means sessions from before Claude Code saved this.")
    print("A different ID only says you were in a test group. Compare its numbers with 'none' to see if anything changed.")
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nSaved the table to {args.csv}. It holds numbers only: no prompts, code or file names.")


if __name__ == "__main__":
    main()
