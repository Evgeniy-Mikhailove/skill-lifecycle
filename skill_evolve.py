#!/usr/bin/env python3
"""
Skill Evolution -- keep skills alive by recording lessons learned.

Appends structured lessons and deprecation notices directly into SKILL.md
files, and maintains a separate evolution log for cross-skill history.

Commands:
  learn      Record a problem/solution pair as a lesson in a skill.
  deprecate  Mark an approach as outdated and point to its replacement.
  history    Show the evolution log for one skill or all skills.
  stale      Find skills whose SKILL.md has not been modified in N days.

Usage:
  python skill_evolve.py learn <skill_id> "<problem>" "<solution>"
  python skill_evolve.py deprecate <skill_id> "<what>" "<replacement>"
  python skill_evolve.py history [skill_id]
  python skill_evolve.py stale [days]
"""

import json, sys, io, re
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import SKILLS_DIR, EVOLUTION_LOG, REGISTRY_PATH


# ---------------------------------------------------------------------------
# Skill-path resolution
# ---------------------------------------------------------------------------

def find_skill_path(skill_id):
    """Locate the SKILL.md file for a given skill id."""
    direct = SKILLS_DIR / skill_id / "SKILL.md"
    if direct.exists():
        return direct

    # Check inside a cybersecurity sub-package if present
    cyber = SKILLS_DIR / "cybersecurity-skills" / "skills" / skill_id / "SKILL.md"
    if cyber.exists():
        return cyber

    return None


# ---------------------------------------------------------------------------
# learn command
# ---------------------------------------------------------------------------

def add_lesson(skill_id, problem, solution):
    """Append a lesson-learned entry to a skill's SKILL.md and to the log."""
    skill_path = find_skill_path(skill_id)
    if not skill_path:
        print(f"ERROR: Skill not found: {skill_id}")
        sys.exit(1)

    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    today = datetime.now().strftime("%Y-%m-%d")
    lesson_entry = f"\n### [{today}] {problem}\n**Problem:** {problem}\n**Solution:** {solution}\n"

    if "## Lessons Learned" in content:
        content = content.replace(
            "## Lessons Learned",
            f"## Lessons Learned{lesson_entry}",
            1,
        )
    else:
        content = content.rstrip() + f"\n\n## Lessons Learned\n{lesson_entry}"

    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(content)

    log_entry = {
        "date": today,
        "skill": skill_id,
        "action": "learn",
        "problem": problem[:200],
        "solution": solution[:200],
    }
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"Lesson added to {skill_id}:")
    print(f"  Problem:  {problem[:100]}")
    print(f"  Solution: {solution[:100]}")
    print(f"  File: {skill_path}")


# ---------------------------------------------------------------------------
# deprecate command
# ---------------------------------------------------------------------------

def deprecate_approach(skill_id, what, replacement):
    """Mark an approach as deprecated inside the skill's SKILL.md."""
    skill_path = find_skill_path(skill_id)
    if not skill_path:
        print(f"ERROR: Skill not found: {skill_id}")
        sys.exit(1)

    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    today = datetime.now().strftime("%Y-%m-%d")
    deprecation = f"\n### [{today}] DEPRECATED: {what}\n**Was:** {what}\n**Use instead:** {replacement}\n"

    if "## Deprecated Approaches" in content:
        content = content.replace(
            "## Deprecated Approaches",
            f"## Deprecated Approaches{deprecation}",
            1,
        )
    else:
        if "## Lessons Learned" in content:
            content = content.replace(
                "## Lessons Learned",
                f"## Deprecated Approaches{deprecation}\n\n## Lessons Learned",
            )
        else:
            content = content.rstrip() + f"\n\n## Deprecated Approaches\n{deprecation}"

    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(content)

    log_entry = {
        "date": today,
        "skill": skill_id,
        "action": "deprecate",
        "what": what[:200],
        "replacement": replacement[:200],
    }
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"Deprecated in {skill_id}:")
    print(f"  Was:         {what[:100]}")
    print(f"  Use instead: {replacement[:100]}")


# ---------------------------------------------------------------------------
# history command
# ---------------------------------------------------------------------------

def show_history(skill_id=None):
    """Display the evolution log, optionally filtered to one skill."""
    if not EVOLUTION_LOG.exists():
        print("No evolution history yet.")
        return

    with open(EVOLUTION_LOG, "r", encoding="utf-8") as f:
        entries = []
        for line in f:
            line = line.strip()
            if line:
                try:
                    e = json.loads(line)
                    if skill_id is None or e.get("skill") == skill_id:
                        entries.append(e)
                except json.JSONDecodeError:
                    pass

    if not entries:
        if skill_id:
            print(f"No evolution history for: {skill_id}")
        else:
            print("No evolution history yet.")
        return

    title = f"Evolution history for: {skill_id}" if skill_id else "All evolution history"
    print(f"{title} ({len(entries)} entries)")
    print()

    for e in entries:
        action = e.get("action", "?")
        if action == "learn":
            print(f"  [{e['date']}] LEARN: {e['skill']}")
            print(f"    Problem:  {e.get('problem', '')[:80]}")
            print(f"    Solution: {e.get('solution', '')[:80]}")
        elif action == "deprecate":
            print(f"  [{e['date']}] DEPRECATE: {e['skill']}")
            print(f"    Was:         {e.get('what', '')[:80]}")
            print(f"    Use instead: {e.get('replacement', '')[:80]}")
        print()


# ---------------------------------------------------------------------------
# stale command
# ---------------------------------------------------------------------------

def find_stale(days=90):
    """List skills whose SKILL.md has not been modified in more than N days."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    stale = []

    for skill in registry["skills"]:
        if skill.get("priority") == "duplicate":
            continue
        skill_path = find_skill_path(skill["id"])
        if skill_path and skill_path.exists():
            mtime = datetime.fromtimestamp(skill_path.stat().st_mtime).strftime("%Y-%m-%d")
            if mtime < cutoff:
                stale.append({
                    "id": skill["id"],
                    "group": skill.get("group", "?"),
                    "last_modified": mtime,
                })

    if stale:
        stale.sort(key=lambda x: x["last_modified"])
        print(f"Stale skills (not modified in {days}+ days): {len(stale)}")
        print()
        for s in stale[:20]:
            print(f"  {s['id']:40s} [{s['group']:20s}] last: {s['last_modified']}")
        if len(stale) > 20:
            print(f"  ... and {len(stale) - 20} more")
    else:
        print(f"No stale skills (all modified within {days} days).")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "learn" and len(sys.argv) >= 5:
        add_lesson(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "deprecate" and len(sys.argv) >= 5:
        deprecate_approach(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "history":
        show_history(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "stale":
        find_stale(int(sys.argv[2]) if len(sys.argv) > 2 else 90)
    else:
        print(__doc__)
