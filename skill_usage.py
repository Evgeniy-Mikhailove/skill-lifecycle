#!/usr/bin/env python3
"""
Skill Usage Tracker -- log and analyze how skills are used.

Appends structured JSON-lines to a usage log, then provides analytics:
total counts, success rates, top-N ranking, unused-skill detection, and
a summary report.

Usage:
  python skill_usage.py log <skill_id> "<task_summary>" [outcome]
  python skill_usage.py stats [skill_id]
  python skill_usage.py top [N]
  python skill_usage.py unused
  python skill_usage.py report

Outcomes: success | adjusted | failed  (default: success)

Examples:
  python skill_usage.py log vulnerability-scanner "API security audit" success
  python skill_usage.py log ci-cd-automation "set up GitHub Actions" adjusted
  python skill_usage.py stats vulnerability-scanner
  python skill_usage.py top 10
  python skill_usage.py unused
  python skill_usage.py report
"""

import json, sys, io
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import USAGE_LOG, REGISTRY_PATH


# ---------------------------------------------------------------------------
# Log I/O
# ---------------------------------------------------------------------------

def log_usage(skill_id, task_summary, outcome="success"):
    """Append one usage entry to the log file."""
    if outcome not in ("success", "adjusted", "failed"):
        print(f"ERROR: outcome must be success|adjusted|failed, got: {outcome}")
        sys.exit(1)

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "skill": skill_id,
        "task": task_summary[:200],
        "outcome": outcome,
    }

    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Logged: {skill_id} [{outcome}] -- {task_summary[:80]}")


def load_log():
    """Read all entries from the usage log."""
    entries = []
    if USAGE_LOG.exists():
        with open(USAGE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


# ---------------------------------------------------------------------------
# Analytics commands
# ---------------------------------------------------------------------------

def show_stats(skill_id=None):
    """Print aggregate statistics, optionally filtered to one skill."""
    entries = load_log()
    if not entries:
        print("No usage data yet.")
        return

    if skill_id:
        entries = [e for e in entries if e["skill"] == skill_id]
        if not entries:
            print(f"No usage data for: {skill_id}")
            return

        print(f"Stats for: {skill_id}")
        print(f"  Total uses:  {len(entries)}")
        outcomes = Counter(e["outcome"] for e in entries)
        for o in ["success", "adjusted", "failed"]:
            print(f"  {o:12s}: {outcomes.get(o, 0)}")
        if outcomes.get("success", 0) + outcomes.get("adjusted", 0) > 0:
            total = len(entries)
            success_rate = (outcomes.get("success", 0) / total) * 100
            print(f"  Success rate: {success_rate:.0f}%")
        print(f"\n  First used: {entries[0]['date']}")
        print(f"  Last used:  {entries[-1]['date']}")
        print(f"\n  Recent tasks:")
        for e in entries[-5:]:
            print(f"    [{e['date']}] {e['outcome']:8s} -- {e['task'][:70]}")
    else:
        print(f"Total entries: {len(entries)}")
        skill_counts = Counter(e["skill"] for e in entries)
        outcomes = Counter(e["outcome"] for e in entries)
        print(f"Unique skills used: {len(skill_counts)}")
        print(
            f"Outcomes: success={outcomes.get('success', 0)} "
            f"adjusted={outcomes.get('adjusted', 0)} "
            f"failed={outcomes.get('failed', 0)}"
        )

        last_7 = [
            e for e in entries
            if e["date"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        ]
        last_30 = [
            e for e in entries
            if e["date"] >= (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        ]
        print(f"Last 7 days: {len(last_7)} uses")
        print(f"Last 30 days: {len(last_30)} uses")


def show_top(n=10):
    """Show the N most-used skills."""
    entries = load_log()
    if not entries:
        print("No usage data yet.")
        return

    skill_counts = Counter(e["skill"] for e in entries)
    print(f"Top {n} most used skills:")
    for i, (skill, count) in enumerate(skill_counts.most_common(n), 1):
        outcomes = Counter(e["outcome"] for e in entries if e["skill"] == skill)
        bar = "#" * min(count, 30)
        status = (
            f"s:{outcomes.get('success', 0)} "
            f"a:{outcomes.get('adjusted', 0)} "
            f"f:{outcomes.get('failed', 0)}"
        )
        print(f"  {i:2d}. {skill:40s} {count:3d} {bar}  ({status})")


def show_unused():
    """List skills that appear in the registry but have never been logged."""
    entries = load_log()
    used_skills = {e["skill"] for e in entries}

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    all_skills = {s["id"] for s in registry["skills"] if s.get("priority") != "duplicate"}
    unused = all_skills - used_skills

    print(f"Never used ({len(unused)} of {len(all_skills)}):")
    by_group = defaultdict(list)
    skill_map = {s["id"]: s for s in registry["skills"]}
    for sid in sorted(unused):
        g = skill_map.get(sid, {}).get("group", "unknown")
        by_group[g].append(sid)

    for group in sorted(by_group.keys()):
        skills = by_group[group]
        print(f"\n  [{group}] ({len(skills)}):")
        for s in skills[:8]:
            print(f"    - {s}")
        if len(skills) > 8:
            print(f"    ... and {len(skills) - 8} more")


def show_report():
    """Print a full summary report combining stats, top skills, and issues."""
    entries = load_log()
    if not entries:
        print("No usage data yet. Start logging with: skill_usage.py log <skill> \"<task>\" <outcome>")
        return

    print("=" * 60)
    print("  SKILL USAGE REPORT")
    print("=" * 60)
    show_stats()
    print()
    show_top(5)
    print()

    adjusted = [e for e in entries if e["outcome"] == "adjusted"]
    if adjusted:
        print(f"Skills that needed adjustment ({len(adjusted)} times):")
        adj_skills = Counter(e["skill"] for e in adjusted)
        for skill, count in adj_skills.most_common(5):
            print(f"  {skill}: {count}x -- consider evolving this skill")
    print()

    failed = [e for e in entries if e["outcome"] == "failed"]
    if failed:
        print(f"Failed applications ({len(failed)}):")
        fail_skills = Counter(e["skill"] for e in failed)
        for skill, count in fail_skills.most_common(5):
            print(f"  {skill}: {count}x -- needs review or retirement")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "log" and len(sys.argv) >= 4:
        outcome = sys.argv[4] if len(sys.argv) > 4 else "success"
        log_usage(sys.argv[2], sys.argv[3], outcome)
    elif cmd == "stats":
        show_stats(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "top":
        show_top(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif cmd == "unused":
        show_unused()
    elif cmd == "report":
        show_report()
    else:
        print(__doc__)
