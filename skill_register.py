#!/usr/bin/env python3
"""
Skill Register -- auto-categorize and register new skills.

Reads a SKILL.md file, extracts frontmatter (name, description, tags),
auto-determines the best group from the registry taxonomy, generates
trigger keywords, and writes the entry to three locations:
  1. REGISTRY.json  (structured catalog)
  2. INDEX.md       (human-readable table)
  3. ROUTER_REGISTRY.md (routing table with trigger keywords)

Usage:
  python skill_register.py <path-to-skill-or-directory>
  python skill_register.py /path/to/skills/my-skill/
  python skill_register.py /path/to/skills/my-skill/SKILL.md
"""

import json, sys, re, io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import SKILLS_DIR, REGISTRY_PATH, INDEX_PATH, ROUTER_PATH


# ---------------------------------------------------------------------------
# Group keyword taxonomy for auto-categorization
# ---------------------------------------------------------------------------

GROUP_KEYWORDS = {
    "content-marketing": [
        "post", "copy", "sales", "marketing", "social", "telegram", "bot",
        "content", "ads", "newsletter", "email", "funnel", "pitch",
        "outreach", "SEO",
    ],
    "design-media": [
        "design", "UI", "UX", "CSS", "frontend", "canvas", "poster",
        "visual", "image", "art", "typography", "color", "layout",
        "responsive", "animation", "prompt", "midjourney",
        "stable diffusion", "dall-e",
    ],
    "automation-api": [
        "API", "webhook", "OAuth", "integration", "n8n", "automation",
        "workflow", "MCP", "REST", "GraphQL", "endpoint",
    ],
    "coding-dev": [
        "Python", "JavaScript", "TypeScript", "React", "Node", "Go",
        "Rust", "backend", "frontend", "fullstack", "database", "SQL",
        "architecture", "code", "script", "library", "framework",
    ],
    "review-debug-security": [
        "review", "bug", "security", "audit", "vulnerability", "pentest",
        "OWASP", "scanning", "lint", "static analysis",
    ],
    "planning-management": [
        "plan", "project", "roadmap", "timeline", "stakeholder", "risk",
        "budget", "scope", "sprint", "agile", "OKR", "KPI", "ROI",
        "career",
    ],
    "files-documents": [
        "Excel", "Word", "PDF", "PowerPoint", "document", "spreadsheet",
        "xlsx", "docx", "pptx", "csv",
    ],
    "ai-ml-agents": [
        "AI", "ML", "LLM", "agent", "RAG", "vector", "embedding",
        "fine-tuning", "prompt", "GPT", "Claude", "model", "inference",
        "training", "neural", "NLP", "transformer",
    ],
    "research-analytics": [
        "research", "analysis", "market", "trend", "competitor", "data",
        "statistics", "forecast", "survey", "benchmark",
    ],
    "obsidian-knowledge": [
        "Obsidian", "vault", "markdown", "wikilink", "callout",
        "frontmatter", "canvas", "graph", "knowledge", "note", "tag",
    ],
    "code-quality": [
        "test", "TDD", "debug", "refactor", "lint", "coverage", "CI",
        "quality", "methodology", "spec", "spike", "PoC",
    ],
    "orchestration-meta": [
        "Claude Code", "skill", "agent", "session", "context", "hook",
        "orchestration", "worktree", "subagent", "memory", "pipeline",
    ],
    "devops-cicd": [
        "Docker", "CI/CD", "deploy", "Kubernetes", "container",
        "pipeline", "GitHub Actions", "Railway", "Vercel", "VPS",
        "release", "rollback", "feature flag",
    ],
    "cybersecurity": [
        "cybersecurity", "MITRE", "ATT&CK", "NIST", "forensic",
        "malware", "threat", "incident", "SOC", "SIEM", "EDR",
        "phishing", "ransomware", "exploit",
    ],
}


# ---------------------------------------------------------------------------
# SKILL.md parser
# ---------------------------------------------------------------------------

def parse_skill_md(path):
    """Parse frontmatter and overview section from a SKILL.md file."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = {}
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.split("\n"):
            m = re.match(r"(\w[\w-]*):\s*(.+)", line)
            if m:
                key, val = m.group(1), m.group(2).strip().strip("'\"")
                frontmatter[key] = val

        tags = []
        in_tags = False
        for line in fm_text.split("\n"):
            if re.match(r"tags:", line):
                in_tags = True
                continue
            if in_tags:
                m = re.match(r"\s*-\s*(.+)", line)
                if m:
                    tags.append(m.group(1).strip())
                else:
                    in_tags = False
        if tags:
            frontmatter["tags"] = tags

    body = content[fm_match.end():] if fm_match else content
    overview = ""
    ov_match = re.search(r"##\s*Overview\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
    if ov_match:
        overview = ov_match.group(1).strip()[:300]

    return frontmatter, overview


# ---------------------------------------------------------------------------
# Auto-categorization helpers
# ---------------------------------------------------------------------------

def determine_group(name, description, tags, overview):
    """Pick the best group by keyword overlap."""
    text = f"{name} {description} {' '.join(tags)} {overview}".lower()
    scores = {}

    for group, keywords in GROUP_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        scores[group] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "coding-dev"
    return best


def generate_triggers(name, description, tags):
    """Generate trigger keywords from tags, description, and skill name."""
    triggers = list(tags[:5]) if tags else []

    stop_words = {
        "this", "that", "with", "from", "when", "your", "used", "using",
        "skill", "should", "before", "after", "which", "about", "more",
        "also", "very", "like", "just", "only", "most", "each", "will",
        "have", "been", "does", "need", "make", "into", "over", "such",
        "than", "them", "then", "some",
    }
    desc_words = re.findall(r"[a-zA-Z0-9-]{4,}", description)
    for w in desc_words:
        if w.lower() not in stop_words and w.lower() not in [t.lower() for t in triggers]:
            triggers.append(w.lower())
        if len(triggers) >= 8:
            break

    name_parts = name.split("-")
    for p in name_parts:
        if len(p) > 3 and p not in [t.lower() for t in triggers]:
            triggers.append(p)
        if len(triggers) >= 10:
            break

    return triggers[:10]


# ---------------------------------------------------------------------------
# Writers -- one per target file
# ---------------------------------------------------------------------------

def add_to_registry(entry):
    """Add or update a skill entry in REGISTRY.json."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    for existing in registry["skills"]:
        if existing["id"] == entry["id"]:
            print(f"  [REGISTRY.json] UPDATED existing entry: {entry['id']}")
            existing.update(entry)
            break
    else:
        registry["skills"].append(entry)
        registry["total_individual_skills"] = len(registry["skills"])
        registry["total_with_packages"] = registry["total_individual_skills"] + sum(
            p.get("total_skills", 0) for p in registry.get("packages", [])
        )
        registry["updated"] = datetime.now().strftime("%Y-%m-%d")
        print(f"  [REGISTRY.json] ADDED new entry: {entry['id']}")

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def add_to_index(skill_id, runtime, source, path):
    """Add a row to INDEX.md if not already present."""
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if f"`{skill_id}`" in content:
        print(f"  [INDEX.md] Already exists: {skill_id}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    new_row = f"| `{skill_id}` | `{runtime}` | `{today}` | `{source}` | `ok` | `{path}` | `{path}` |"

    marker = "## Packages"
    if marker in content:
        content = content.replace(marker, f"{new_row}\n\n{marker}")
    else:
        content = content.rstrip() + "\n" + new_row + "\n"

    count_match = re.search(r"Total skills:\s*(\d+)", content)
    if count_match:
        old_count = int(count_match.group(1))
        content = content.replace(f"Total skills: {old_count}", f"Total skills: {old_count + 1}")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [INDEX.md] ADDED: {skill_id}")


def add_to_router(skill_id, group, triggers):
    """Add a row to ROUTER_REGISTRY.md under the correct group section."""
    with open(ROUTER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if f"`{skill_id}`" in content:
        print(f"  [ROUTER_REGISTRY.md] Already exists: {skill_id}")
        return

    # Map group IDs to section headers in the router file.
    # These are generic English headers -- adjust if your ROUTER_REGISTRY.md
    # uses different section names.
    group_to_section = {
        "content-marketing": "### Content / Marketing / Sales",
        "design-media": "### Design / Media / Image Generation",
        "automation-api": "### Automation / API",
        "coding-dev": "### Coding / Development",
        "review-debug-security": "### Review / Debug / Security",
        "planning-management": "### Planning / Management",
        "files-documents": "### Files / Documents",
        "ai-ml-agents": "### AI / ML / Agents / Prompting",
        "research-analytics": "### Research / Analytics / Market",
        "obsidian-knowledge": "### Obsidian / Knowledge Base",
        "code-quality": "### Code Quality / Methodologies",
        "orchestration-meta": "### Orchestration / Skills / Claude Code",
        "devops-cicd": "### DevOps / CI/CD / Deploy",
        "cybersecurity": "### Cybersecurity",
    }

    section_header = group_to_section.get(group)
    if not section_header:
        print(f"  [ROUTER_REGISTRY.md] Unknown group: {group}, skipping")
        return

    trigger_str = ", ".join(triggers[:5])
    new_row = f"| `{skill_id}` | conditional | - | {trigger_str} |"

    if section_header in content:
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if section_header in line:
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("###") or lines[j].startswith("---") or (
                        lines[j].strip() == "" and j + 1 < len(lines) and lines[j + 1].startswith("###")
                    ):
                        insert_idx = j
                        break
                    if (
                        lines[j].startswith("|")
                        and not lines[j].startswith("|--")
                        and not lines[j].startswith("| skill")
                        and not lines[j].startswith("| subdomain")
                    ):
                        insert_idx = j + 1
                if insert_idx is None:
                    insert_idx = len(lines)
                break

        if insert_idx:
            lines.insert(insert_idx, new_row)
            content = "\n".join(lines)
    else:
        # Section does not exist yet -- append a new one before a DUPLICATES
        # section if present, otherwise at the end.
        before_dupes = "### DUPLICATES"
        if before_dupes in content:
            content = content.replace(
                before_dupes,
                f"{section_header}\n| skill | primary | fallback | trigger |\n|-------|---------|---------|---------|"
                f"\n{new_row}\n\n{before_dupes}",
            )
        else:
            content = content.rstrip() + (
                f"\n\n{section_header}\n| skill | primary | fallback | trigger |\n"
                f"|-------|---------|---------|---------|"
                f"\n{new_row}\n"
            )

    with open(ROUTER_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [ROUTER_REGISTRY.md] ADDED to '{group}': {skill_id}")


# ---------------------------------------------------------------------------
# Main registration workflow
# ---------------------------------------------------------------------------

def register(skill_path_str):
    """Full registration pipeline for one skill."""
    skill_path = Path(skill_path_str).resolve()

    if skill_path.is_dir():
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            print(f"ERROR: No SKILL.md found in {skill_path}")
            sys.exit(1)
        skill_path = skill_md

    if not skill_path.exists():
        print(f"ERROR: File not found: {skill_path}")
        sys.exit(1)

    print(f"Registering: {skill_path}")
    print()

    frontmatter, overview = parse_skill_md(skill_path)

    skill_id = frontmatter.get("name", skill_path.parent.name)
    description = frontmatter.get("description", "")
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    runtime = "claude-only"
    source = "manual-install"
    path = str(skill_path).replace("\\", "/")

    group = determine_group(skill_id, description, tags, overview)
    triggers = generate_triggers(skill_id, description, tags)

    print(f"  Skill ID:    {skill_id}")
    print(f"  Description: {description[:100]}")
    print(f"  Group:       {group}")
    print(f"  Triggers:    {', '.join(triggers[:5])}")
    print()

    entry = {
        "id": skill_id,
        "description": description,
        "group": group,
        "priority": "conditional",
        "triggers": triggers,
        "runtime": runtime,
        "source": source,
        "path": path,
    }

    add_to_registry(entry)
    add_to_index(skill_id, runtime, source, path)
    add_to_router(skill_id, group, triggers)

    print()
    print(f"DONE. Skill '{skill_id}' fully registered in all 3 locations.")
    print(f"  Group: {group}")
    print(f"  Triggers: {', '.join(triggers[:5])}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skill_register.py <path-to-skill-or-SKILL.md>")
        sys.exit(1)

    register(sys.argv[1])
