"""
Skill Lifecycle — path configuration.

All paths are resolved automatically from your Claude Code installation.
Override any path by setting environment variables or editing config.json.
"""

import os
import json
from pathlib import Path


def _find_claude_home():
    """Find the .claude directory — works on macOS, Linux, and Windows."""
    env = os.environ.get("SKILL_LIFECYCLE_HOME")
    if env:
        return Path(env)

    home = Path.home()
    candidates = [
        home / ".claude",
        home / ".config" / "claude",
    ]
    for c in candidates:
        if c.exists():
            return c

    return home / ".claude"


def _load_config():
    """Load optional config.json overrides."""
    config_path = ORCH_DIR / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


CLAUDE_HOME = _find_claude_home()
SKILLS_DIR = CLAUDE_HOME / "skills"
ORCH_DIR = CLAUDE_HOME / "orchestration"

_overrides = _load_config()

REGISTRY_PATH = Path(_overrides.get("registry_path", str(ORCH_DIR / "REGISTRY.json")))
INDEX_PATH = Path(_overrides.get("index_path", str(SKILLS_DIR / "INDEX.md")))
ROUTER_PATH = Path(_overrides.get("router_path", str(ORCH_DIR / "ROUTER_REGISTRY.md")))
USAGE_LOG = Path(_overrides.get("usage_log", str(ORCH_DIR / "usage.log")))
EVOLUTION_LOG = Path(_overrides.get("evolution_log", str(ORCH_DIR / "evolution.log")))
CANVAS_OUTPUT = Path(_overrides.get("canvas_output", str(SKILLS_DIR / "skill-ecosystem.canvas")))
