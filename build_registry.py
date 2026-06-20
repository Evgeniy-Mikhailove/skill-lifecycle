#!/usr/bin/env python3
"""
Build Registry -- generate REGISTRY.json from skills on disk.

Scans the skills directory for SKILL.md files, parses their frontmatter
to extract descriptions and tags, auto-categorizes each skill into a
group, generates trigger keywords, and writes a unified REGISTRY.json.

Unlike a hardcoded router map, this version is fully dynamic: it reads
whatever skills exist on disk and derives all metadata from their
SKILL.md files.  To add a new skill, just drop it into the skills
directory and re-run this script.

Duplicate detection is configurable via a duplicates.json file placed
next to REGISTRY.json (optional).

Usage:
  python build_registry.py
  python build_registry.py --include-packages   # also scan package dirs
"""

import json, sys, re, io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import SKILLS_DIR, REGISTRY_PATH, INDEX_PATH


# ---------------------------------------------------------------------------
# Group definitions
# ---------------------------------------------------------------------------

GROUPS = [
    {"id": "content-marketing", "name": "Content / Marketing / Sales"},
    {"id": "design-media", "name": "Design / Media / Image Generation"},
    {"id": "automation-api", "name": "Automation / API"},
    {"id": "coding-dev", "name": "Coding / Development"},
    {"id": "review-debug-security", "name": "Review / Debug / Security"},
    {"id": "planning-management", "name": "Planning / Management"},
    {"id": "files-documents", "name": "Files / Documents"},
    {"id": "ai-ml-agents", "name": "AI / ML / Agents / Prompting"},
    {"id": "research-analytics", "name": "Research / Analytics / Market"},
    {"id": "obsidian-knowledge", "name": "Obsidian / Knowledge Base"},
    {"id": "code-quality", "name": "Code Quality / Methodologies"},
    {"id": "orchestration-meta", "name": "Orchestration / Skills / Claude Code"},
    {"id": "devops-cicd", "name": "DevOps / CI/CD / Deploy"},
    {"id": "cybersecurity", "name": "Cybersecurity"},
]

# Pattern-based auto-grouping: if the skill ID contains the pattern,
# assign it to the corresponding group.
AUTO_GROUP_PATTERNS = {
    "agent": "ai-ml-agents",
    "ai-": "ai-ml-agents",
    "llm": "ai-ml-agents",
    "prompt": "ai-ml-agents",
    "n8n": "automation-api",
    "api": "automation-api",
    "webhook": "automation-api",
    "mcp": "automation-api",
    "design": "design-media",
    "ui-": "design-media",
    "frontend": "design-media",
    "css": "design-media",
    "obsidian": "obsidian-knowledge",
    "canvas": "obsidian-knowledge",
    "graph": "obsidian-knowledge",
    "test": "code-quality",
    "debug": "code-quality",
    "refactor": "code-quality",
    "review": "review-debug-security",
    "security": "review-debug-security",
    "bug": "review-debug-security",
    "vuln": "review-debug-security",
    "senior-": "coding-dev",
    "python": "coding-dev",
    "javascript": "coding-dev",
    "typescript": "coding-dev",
    "coding": "coding-dev",
    "clean-arch": "coding-dev",
    "git": "devops-cicd",
    "ci": "devops-cicd",
    "deploy": "devops-cicd",
    "docker": "devops-cicd",
    "ship": "devops-cicd",
    "release": "devops-cicd",
    "worktree": "devops-cicd",
    "doc": "files-documents",
    "xlsx": "files-documents",
    "pdf": "files-documents",
    "pptx": "files-documents",
    "excel": "files-documents",
    "plan": "planning-management",
    "project": "planning-management",
    "business": "planning-management",
    "career": "planning-management",
    "market": "research-analytics",
    "research": "research-analytics",
    "stock": "research-analytics",
    "trend": "research-analytics",
    "arxiv": "research-analytics",
    "copy": "content-marketing",
    "sales": "content-marketing",
    "social": "content-marketing",
    "telegram": "content-marketing",
    "content": "content-marketing",
    "claude": "orchestration-meta",
    "skill": "orchestration-meta",
    "session": "orchestration-meta",
    "context": "orchestration-meta",
    "orchestr": "orchestration-meta",
    "workflow": "orchestration-meta",
    "hook": "orchestration-meta",
    "memory": "orchestration-meta",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def auto_group(skill_id):
    """Determine group from the skill ID via pattern matching."""
    for pattern, group in AUTO_GROUP_PATTERNS.items():
        if pattern in skill_id:
            return group
    return "coding-dev"


def read_skill_md(skill_md_path):
    """Read frontmatter fields from a SKILL.md file."""
    result = {"description": "", "tags": [], "name": ""}
    if not skill_md_path.exists():
        return result

    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read(2000)

    # Description from frontmatter
    m = re.search(r"description:\s*['\"]?(.+?)['\"]?\s*\n", content)
    if m:
        result["description"] = m.group(1).strip().strip("'\"")

    # Name from frontmatter
    m = re.search(r"name:\s*['\"]?(.+?)['\"]?\s*\n", content)
    if m:
        result["name"] = m.group(1).strip().strip("'\"")

    # Tags from frontmatter (YAML list)
    tags = []
    in_tags = False
    for line in content.split("\n"):
        if re.match(r"tags:", line):
            in_tags = True
            continue
        if in_tags:
            tm = re.match(r"\s*-\s*(.+)", line)
            if tm:
                tags.append(tm.group(1).strip())
            else:
                in_tags = False
    result["tags"] = tags

    return result


def extract_triggers(description, skill_id, tags):
    """Generate trigger keywords from description, skill ID, and tags."""
    triggers = list(tags[:5])

    stop_words = {
        "with", "from", "this", "that", "when", "your", "skill",
        "claude", "used", "using", "should", "before", "after",
        "which", "about", "more", "also", "very", "like", "just",
        "only", "most", "each", "will", "have", "been", "does",
        "need", "make", "into", "over", "such", "than", "them",
        "then", "some",
    }
    words = re.findall(r"[a-zA-Z0-9-]+", f"{description} {skill_id}")
    for w in words:
        w_lower = w.lower()
        if len(w_lower) > 3 and w_lower not in stop_words and w_lower not in [t.lower() for t in triggers]:
            triggers.append(w_lower)
        if len(triggers) >= 8:
            break

    return list(dict.fromkeys(triggers))[:8]


def load_duplicates():
    """Load an optional duplicates.json mapping from the same directory as REGISTRY."""
    dupes_path = REGISTRY_PATH.parent / "duplicates.json"
    if dupes_path.exists():
        with open(dupes_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def read_index_md():
    """Parse INDEX.md for existing skill metadata."""
    skills = {}
    if not INDEX_PATH.exists():
        return skills
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(
                r"\|\s*`([a-z][a-z0-9-]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*"
                r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
                line,
            )
            if m:
                sid, runtime, updated, source, status, canonical, path = m.groups()
                skills[sid] = {
                    "runtime": runtime,
                    "updated": updated,
                    "source": source,
                    "status": status,
                    "path": path,
                }
    return skills


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build(include_packages=False):
    """Scan skills on disk and build REGISTRY.json."""
    duplicates = load_duplicates()
    index_skills = read_index_md()

    # Discover all skills on disk
    disk_skills = {}
    if SKILLS_DIR.exists():
        for item in sorted(SKILLS_DIR.iterdir()):
            if item.is_dir() and (item / "SKILL.md").exists():
                # Skip package directories unless requested
                if item.name == "cybersecurity-skills" and not include_packages:
                    continue
                disk_skills[item.name] = item / "SKILL.md"

    all_skills = []

    for sid, skill_md_path in disk_skills.items():
        meta = read_skill_md(skill_md_path)
        index_meta = index_skills.get(sid, {})

        runtime = index_meta.get("runtime", "claude-only")
        source = index_meta.get("source", "disk-scan")
        path = index_meta.get("path", str(skill_md_path).replace("\\", "/"))

        if sid in duplicates:
            entry = {
                "id": sid,
                "description": meta["description"],
                "group": auto_group(sid),
                "priority": "duplicate",
                "replaces_by": duplicates[sid],
                "triggers": [],
                "runtime": runtime,
                "source": source,
                "path": path,
            }
        else:
            group = auto_group(sid)
            triggers = extract_triggers(meta["description"], sid, meta["tags"])
            entry = {
                "id": sid,
                "description": meta["description"],
                "group": group,
                "priority": "conditional",
                "triggers": triggers,
                "runtime": runtime,
                "source": source,
                "path": path,
            }

        all_skills.append(entry)

    # Package detection (cybersecurity or similar)
    packages = []
    cyber_dir = SKILLS_DIR / "cybersecurity-skills"
    if cyber_dir.exists():
        cyber_index = cyber_dir / "index.json"
        cyber_subdomains = []
        total_cyber = 0

        if cyber_index.exists():
            with open(cyber_index, "r", encoding="utf-8") as f:
                cyber_data = json.load(f)
            cyber_skills_list = cyber_data.get("skills", [])
            total_cyber = len(cyber_skills_list)

            sd_map = {}
            for cs in cyber_skills_list:
                skill_md = cyber_dir / cs.get("path", "") / "SKILL.md"
                sd = "general"
                if skill_md.exists():
                    with open(skill_md, "r", encoding="utf-8") as f:
                        head = f.read(500)
                    m = re.search(r"subdomain:\s*(.+)", head)
                    if m:
                        sd = m.group(1).strip()
                sd_map[sd] = sd_map.get(sd, 0) + 1
            cyber_subdomains = [
                {"name": k, "count": v}
                for k, v in sorted(sd_map.items(), key=lambda x: -x[1])
            ]

        packages.append({
            "id": "cybersecurity-skills",
            "description": "Cybersecurity skill package",
            "total_skills": total_cyber,
            "index_path": str(cyber_index).replace("\\", "/"),
            "skills_dir": str(cyber_dir / "skills").replace("\\", "/"),
            "subdomains": cyber_subdomains,
        })

    package_total = sum(p.get("total_skills", 0) for p in packages)

    registry = {
        "version": "1.0.0",
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "total_individual_skills": len(all_skills),
        "total_with_packages": len(all_skills) + package_total,
        "groups": GROUPS,
        "skills": all_skills,
        "packages": packages,
    }

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"REGISTRY.json built: {len(all_skills)} individual skills + {len(packages)} package(s) ({package_total} skills)")
    groups_count = {}
    for s in all_skills:
        g = s["group"]
        groups_count[g] = groups_count.get(g, 0) + 1
    for g, c in sorted(groups_count.items(), key=lambda x: -x[1]):
        print(f"  {g}: {c}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    include_packages = "--include-packages" in sys.argv
    build(include_packages=include_packages)
