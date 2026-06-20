#!/usr/bin/env python3
"""
Install Skill Lifecycle tools into your Claude Code orchestration directory.

Usage:
    python install.py              # Install to ~/.claude/orchestration/
    python install.py --check      # Verify installation without copying
    python install.py --uninstall  # Remove installed files
"""

import sys
import shutil
from pathlib import Path

TOOLS = [
    "config.py",
    "skill_router.py",
    "skill_register.py",
    "skill_usage.py",
    "skill_evolve.py",
    "audit.py",
    "build_registry.py",
    "build_canvas.py",
]

PROTOCOL = "SKILL_LIFECYCLE_PROTOCOL.md"


def find_target():
    home = Path.home()
    candidates = [
        home / ".claude" / "orchestration",
        home / ".config" / "claude" / "orchestration",
    ]
    for c in candidates:
        if c.parent.exists():
            c.mkdir(exist_ok=True)
            return c

    default = home / ".claude" / "orchestration"
    default.mkdir(parents=True, exist_ok=True)
    return default


def install(target):
    source = Path(__file__).parent
    copied = 0

    for tool in TOOLS:
        src = source / tool
        dst = target / tool
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied: {tool}")
            copied += 1
        else:
            print(f"  Missing: {tool} (skipped)")

    proto_src = source / PROTOCOL
    if proto_src.exists():
        shutil.copy2(proto_src, target / PROTOCOL)
        print(f"  Copied: {PROTOCOL}")
        copied += 1

    skills_dir = target.parent / "skills"
    skills_dir.mkdir(exist_ok=True)

    return copied


def check(target):
    missing = []
    present = []
    for tool in TOOLS:
        if (target / tool).exists():
            present.append(tool)
        else:
            missing.append(tool)

    print(f"Target: {target}")
    print(f"Present: {len(present)}/{len(TOOLS)}")
    if missing:
        print(f"Missing: {', '.join(missing)}")
    else:
        print("All tools installed.")
    return len(missing) == 0


def uninstall(target):
    removed = 0
    for tool in TOOLS + [PROTOCOL]:
        f = target / tool
        if f.exists():
            f.unlink()
            print(f"  Removed: {tool}")
            removed += 1
    print(f"\nRemoved {removed} files.")


def main():
    target = find_target()

    if "--check" in sys.argv:
        ok = check(target)
        sys.exit(0 if ok else 1)
    elif "--uninstall" in sys.argv:
        print(f"Uninstalling from: {target}\n")
        uninstall(target)
    else:
        print(f"Installing to: {target}\n")
        count = install(target)
        print(f"\nInstalled {count} files.")
        print(f"\nNext steps:")
        print(f"  1. Build your registry:  python {target / 'build_registry.py'}")
        print(f"  2. Try the router:       python {target / 'skill_router.py'} \"your task here\"")
        print(f"  3. Run an audit:         python {target / 'audit.py'}")


if __name__ == "__main__":
    main()
