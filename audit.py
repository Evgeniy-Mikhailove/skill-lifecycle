#!/usr/bin/env python3
"""
Skill Audit -- health check for all registered skills.

Compares REGISTRY.json, the skills directory on disk, and INDEX.md to
surface inconsistencies: missing files, orphan skills, empty triggers,
group distribution imbalances, and package integrity.

Modes:
  full   (default)  All checks including cross-file consistency.
  quick  (--quick)  Only verify that registered skills exist on disk.

Usage:
  python audit.py           # Full audit
  python audit.py --quick   # Quick existence check only
"""

import json, sys, os, io, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import SKILLS_DIR, REGISTRY_PATH, INDEX_PATH


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_disk_skills():
    """Return skill IDs present on disk (directories containing SKILL.md)."""
    skills = set()
    if SKILLS_DIR.exists():
        for item in SKILLS_DIR.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.add(item.name)
    return skills


def get_index_skills():
    """Parse INDEX.md for skill IDs."""
    skills = set()
    if not INDEX_PATH.exists():
        return skills
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\|\s*`([a-z][a-z0-9-]+)`\s*\|", line)
            if m:
                skills.add(m.group(1))
    return skills


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------

def audit(quick=False):
    registry = load_registry()
    reg_skills = {s["id"]: s for s in registry["skills"]}
    disk_skills = get_disk_skills()
    index_skills = get_index_skills()

    issues = []
    warnings = []
    stats = {
        "registered": len(reg_skills),
        "on_disk": len(disk_skills),
        "in_index": len(index_skills),
        "packages": len(registry.get("packages", [])),
        "package_skills": sum(p.get("total_skills", 0) for p in registry.get("packages", [])),
    }

    # 1. Registry skills missing from disk
    missing_on_disk = []
    for sid, skill in reg_skills.items():
        skill_path_str = skill.get("path", "")
        if skill_path_str:
            p = Path(skill_path_str.replace("\\", "/"))
            if not p.exists():
                p2 = SKILLS_DIR / sid / "SKILL.md"
                if not p2.exists():
                    missing_on_disk.append(sid)

    if missing_on_disk:
        issues.append(f"MISSING ON DISK ({len(missing_on_disk)}): {', '.join(missing_on_disk[:10])}")

    # 2. Orphan skills (on disk, not in registry)
    # Exclude known package directories from orphan detection.
    excluded_dirs = {"cybersecurity-skills"}
    orphans = disk_skills - set(reg_skills.keys()) - excluded_dirs
    if orphans:
        warnings.append(f"ORPHANS -- on disk but not in REGISTRY ({len(orphans)}): {', '.join(sorted(orphans)[:10])}")

    # 3. Skills without triggers
    no_triggers = [
        s["id"] for s in registry["skills"]
        if not s.get("triggers") and s.get("priority") != "duplicate"
    ]
    if no_triggers:
        warnings.append(f"NO TRIGGERS ({len(no_triggers)}): {', '.join(no_triggers[:10])}")

    if quick:
        print_report(stats, issues, warnings)
        return

    # 4. Registry vs INDEX consistency
    reg_ids = set(reg_skills.keys())
    in_reg_not_index = reg_ids - index_skills
    in_index_not_reg = index_skills - reg_ids - excluded_dirs

    if in_reg_not_index:
        warnings.append(f"IN REGISTRY NOT INDEX ({len(in_reg_not_index)}): {', '.join(sorted(in_reg_not_index)[:10])}")
    if in_index_not_reg:
        warnings.append(f"IN INDEX NOT REGISTRY ({len(in_index_not_reg)}): {', '.join(sorted(in_index_not_reg)[:10])}")

    # 5. Group distribution
    group_counts = {}
    for s in registry["skills"]:
        g = s.get("group", "unknown")
        group_counts[g] = group_counts.get(g, 0) + 1

    # 6. Duplicates check
    dupes = [s for s in registry["skills"] if s.get("priority") == "duplicate"]

    # 7. Package health (generic -- checks first package)
    pkg_health = "N/A"
    for pkg in registry.get("packages", []):
        idx_path = Path(pkg.get("index_path", "").replace("\\", "/"))
        skills_dir = Path(pkg.get("skills_dir", "").replace("\\", "/"))
        if idx_path.exists() and skills_dir.exists():
            actual = len(list(skills_dir.iterdir()))
            expected = pkg.get("total_skills", 0)
            if expected and actual >= expected * 0.95:
                pkg_health = f"OK ({actual}/{expected} skills on disk)"
            elif expected:
                pkg_health = f"PARTIAL ({actual}/{expected} skills on disk)"
                issues.append(f"Package '{pkg['id']}' incomplete: {actual}/{expected}")
        else:
            pkg_health = "MISSING"
            issues.append(f"Package '{pkg['id']}' not found on disk")
        break  # only check first package

    print_report(stats, issues, warnings, group_counts, dupes, pkg_health)


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(stats, issues, warnings, group_counts=None, dupes=None, pkg_health=None):
    print("=" * 60)
    print("  SKILL AUDIT REPORT")
    print("=" * 60)
    print()
    print(f"  Registered skills:  {stats['registered']}")
    print(f"  On disk:            {stats['on_disk']}")
    print(f"  In INDEX.md:        {stats['in_index']}")
    print(f"  Packages:           {stats['packages']} ({stats['package_skills']} skills)")
    print(f"  Total ecosystem:    {stats['registered'] + stats['package_skills']}")
    print()

    if issues:
        print("ISSUES (need attention):")
        for i in issues:
            print(f"  [!] {i}")
        print()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [~] {w}")
        print()

    if group_counts:
        print("GROUP DISTRIBUTION:")
        for g, c in sorted(group_counts.items(), key=lambda x: -x[1]):
            bar = "#" * min(c, 30)
            print(f"  {g:30s} {c:3d} {bar}")
        print()

    if dupes:
        print(f"DUPLICATES ({len(dupes)}):")
        for d in dupes:
            print(f"  {d['id']} -> {d.get('replaces_by', '?')}")
        print()

    if pkg_health:
        print(f"PACKAGE HEALTH: {pkg_health}")
        print()

    if not issues:
        print("STATUS: ALL CLEAR")
    else:
        print(f"STATUS: {len(issues)} ISSUE(S) FOUND")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    audit(quick)
