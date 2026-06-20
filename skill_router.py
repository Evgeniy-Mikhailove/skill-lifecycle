#!/usr/bin/env python3
"""
Skill Router -- smart search across all registered skills.

Scores skills from REGISTRY.json against a natural-language query, returning
three ranked lists: direct matches, potential next-step matches (from
adjacent groups), and cybersecurity-package matches (when relevant).

Supports bilingual queries (English / Russian) via a synonym table.

Usage:
  python skill_router.py "set up CI/CD for a project"
  python skill_router.py --json "run a security audit"
  python skill_router.py --post-task skill1,skill2 "task description"

Modes:
  (default)    Human-readable ranked output.
  --json       Machine-readable JSON.
  --post-task  After completing a task with the listed skills, recommend
               related skills for the logical next step.
"""

import json, sys, re, io
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import REGISTRY_PATH, SKILLS_DIR

CYBER_INDEX = SKILLS_DIR / "cybersecurity-skills" / "index.json"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cyber_index():
    if CYBER_INDEX.exists():
        with open(CYBER_INDEX, "r", encoding="utf-8") as f:
            return json.load(f).get("skills", [])
    return []


# ---------------------------------------------------------------------------
# Bilingual synonym map
# ---------------------------------------------------------------------------

SYNONYMS = {
    "security": ["vulnerability", "audit"],
    "vulnerability": ["security", "exploit"],
    "sql injection": ["sqli", "sql-injection", "injection"],
    "xss": ["cross-site scripting", "xss", "script injection"],
    "test": ["testing"],
    "deploy": ["deployment", "release"],
    "automation": ["automate", "workflow"],
    "code": ["coding"],
    "bot": ["telegram bot", "chatbot"],
    "prompt": ["prompting"],
    "design": ["UI", "UX"],
    "script": ["scripting"],
    "pipeline": ["conveyor"],
    "pentest": ["penetration testing"],
    "forensic": ["forensics", "investigation"],
    "malware": ["virus"],
    "threat": ["threat hunting"],
    "freelance": ["consulting"],
    "sales": ["selling"],
    "post": ["article", "content"],
    "excel": ["xlsx", "spreadsheet"],
    "word": ["docx", "document"],
}


def expand_query(tokens, query_text):
    """Expand a set of query tokens with synonyms."""
    expanded = set(tokens)
    query_lower = query_text.lower()
    for key, synonyms in SYNONYMS.items():
        if key in query_lower or key in expanded:
            expanded.update(s.lower() for s in synonyms)
    return expanded


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize(text):
    return re.sub(r"[^a-z0-9\s-]", "", text.lower())


def tokenize(text):
    return set(re.findall(r"[a-z0-9-]+", normalize(text)))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_skill(skill, query_tokens, query_text):
    """Score a registry skill against expanded query tokens."""
    score = 0.0
    reasons = []

    skill_triggers = [t.lower() for t in skill.get("triggers", [])]
    skill_desc = skill.get("description", "").lower()
    skill_id = skill["id"].lower()
    skill_id_parts = set(skill_id.split("-"))

    for token in query_tokens:
        for trigger in skill_triggers:
            if token in trigger or trigger in query_text.lower():
                score += 3.0
                reasons.append(f"trigger: {trigger}")
                break

        if token in skill_id_parts:
            score += 2.0
            reasons.append(f"id match: {token}")

        if token in skill_desc:
            score += 1.0

    for trigger in skill_triggers:
        trigger_lower = trigger.lower()
        if trigger_lower in query_text.lower():
            score += 4.0
            reasons.append(f"phrase: {trigger_lower}")

    if skill_id in query_text.lower().replace(" ", "-"):
        score += 5.0
        reasons.append("exact id match")

    priority_bonus = {"primary": 1.5, "conditional": 0.5, "fallback": 0.3, "duplicate": -10.0}
    score *= priority_bonus.get(skill.get("priority", "conditional"), 1.0)

    return score, list(dict.fromkeys(reasons))[:3]


def score_cyber_skill(cyber_skill, query_tokens, query_text):
    """Score a cybersecurity-package skill."""
    score = 0.0
    name = cyber_skill.get("name", "").lower()
    desc = cyber_skill.get("description", "").lower()
    name_parts = set(name.split("-"))

    for token in query_tokens:
        if token in name_parts:
            score += 3.0
        if token in desc:
            score += 1.5
        if token in name:
            score += 1.0

    cyber_keywords = [
        "security", "hack", "pentest", "forensic", "malware",
        "threat", "vulnerability", "exploit", "phishing", "ransomware",
        "SIEM", "SOC",
    ]
    if any(t in query_text.lower() for t in cyber_keywords):
        score += 2.0

    return score


# ---------------------------------------------------------------------------
# Group adjacency graph
# ---------------------------------------------------------------------------

GROUP_ADJACENCY = {
    "content-marketing": ["design-media", "research-analytics", "ai-ml-agents"],
    "design-media": ["content-marketing", "coding-dev", "orchestration-meta"],
    "automation-api": ["coding-dev", "devops-cicd", "ai-ml-agents"],
    "coding-dev": ["code-quality", "review-debug-security", "devops-cicd", "automation-api"],
    "review-debug-security": ["coding-dev", "code-quality", "cybersecurity"],
    "planning-management": ["orchestration-meta", "research-analytics", "content-marketing"],
    "files-documents": ["automation-api", "coding-dev", "obsidian-knowledge"],
    "ai-ml-agents": ["coding-dev", "automation-api", "research-analytics", "orchestration-meta"],
    "research-analytics": ["ai-ml-agents", "content-marketing", "planning-management"],
    "obsidian-knowledge": ["files-documents", "orchestration-meta", "research-analytics"],
    "code-quality": ["coding-dev", "review-debug-security", "devops-cicd"],
    "orchestration-meta": ["ai-ml-agents", "automation-api", "code-quality"],
    "devops-cicd": ["coding-dev", "automation-api", "code-quality"],
    "cybersecurity": ["review-debug-security", "devops-cicd", "coding-dev"],
}


# ---------------------------------------------------------------------------
# Main routing logic
# ---------------------------------------------------------------------------

def route(query_text):
    """Route a query to the best-matching skills."""
    registry = load_registry()
    query_tokens = tokenize(query_text)
    expanded_tokens = expand_query(query_tokens, query_text)

    scored = []
    for skill in registry["skills"]:
        sc, reasons = score_skill(skill, expanded_tokens, query_text)
        if sc > 0:
            scored.append({
                "id": skill["id"],
                "group": skill["group"],
                "description": skill.get("description", "")[:120],
                "priority": skill["priority"],
                "score": round(sc, 1),
                "reasons": reasons,
            })

    scored.sort(key=lambda x: -x["score"])

    direct = scored[:5]

    # Find adjacent groups for potential recommendations
    direct_groups = {s["group"] for s in direct}
    adjacent_groups = set()
    for g in direct_groups:
        adjacent_groups.update(GROUP_ADJACENCY.get(g, []))
    adjacent_groups -= direct_groups

    direct_ids = {s["id"] for s in direct}
    potential_candidates = []
    for skill in registry["skills"]:
        if skill["id"] in direct_ids:
            continue
        if skill["priority"] == "duplicate":
            continue
        if skill["group"] in adjacent_groups:
            sc, reasons = score_skill(skill, expanded_tokens, query_text)
            if sc > 0:
                potential_candidates.append({
                    "id": skill["id"],
                    "group": skill["group"],
                    "description": skill.get("description", "")[:120],
                    "score": round(sc, 1),
                    "why_potential": f"adjacent to {', '.join(direct_groups & set(GROUP_ADJACENCY.get(skill['group'], [])))}",
                })

    remaining = [s for s in scored if s["id"] not in direct_ids and s["priority"] != "duplicate"]
    for s in remaining[:10]:
        if s["id"] not in {p["id"] for p in potential_candidates}:
            potential_candidates.append({
                "id": s["id"],
                "group": s["group"],
                "description": s.get("description", "")[:120],
                "score": s["score"],
                "why_potential": "scored but not top-5",
            })

    potential_candidates.sort(key=lambda x: -x["score"])
    potential = potential_candidates[:5]

    # Cybersecurity package search
    cyber_results = []
    cyber_skills = load_cyber_index()
    if cyber_skills:
        cyber_scored = []
        for cs in cyber_skills:
            sc = score_cyber_skill(cs, query_tokens, query_text)
            if sc > 2.0:
                cyber_scored.append({
                    "name": cs["name"],
                    "description": cs.get("description", "")[:120],
                    "path": cs.get("path", ""),
                    "score": round(sc, 1),
                })
        cyber_scored.sort(key=lambda x: -x["score"])
        cyber_results = cyber_scored[:3]

    result = {
        "query": query_text,
        "direct": direct,
        "potential": potential,
    }
    if cyber_results:
        result["cybersecurity"] = cyber_results

    return result


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_output(result):
    lines = [f"Query: {result['query']}", ""]

    lines.append("DIRECT (apply now):")
    if result["direct"]:
        for i, s in enumerate(result["direct"], 1):
            reasons_str = ", ".join(s.get("reasons", []))
            lines.append(f"  {i}. {s['id']} [{s['group']}] (score: {s['score']})")
            lines.append(f"     {s['description']}")
            if reasons_str:
                lines.append(f"     why: {reasons_str}")
    else:
        lines.append("  (no matches)")

    lines.append("")
    lines.append("POTENTIAL (next steps / scaling):")
    if result["potential"]:
        for i, s in enumerate(result["potential"], 1):
            lines.append(f"  {i}. {s['id']} [{s['group']}] (score: {s['score']})")
            lines.append(f"     {s['description']}")
            lines.append(f"     why: {s.get('why_potential', '')}")
    else:
        lines.append("  (no adjacent matches)")

    if result.get("cybersecurity"):
        lines.append("")
        lines.append("CYBERSECURITY PACKAGE:")
        for i, s in enumerate(result["cybersecurity"], 1):
            lines.append(f"  {i}. {s['name']} (score: {s['score']})")
            lines.append(f"     {s['description']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post-task recommendations
# ---------------------------------------------------------------------------

def post_task_recommend(used_skill_ids, task_text):
    """After completing a task, recommend next-step skills."""
    registry = load_registry()
    skill_map = {s["id"]: s for s in registry["skills"]}

    used_groups = set()
    for sid in used_skill_ids:
        if sid in skill_map:
            used_groups.add(skill_map[sid]["group"])

    adjacent_groups = set()
    for g in used_groups:
        adjacent_groups.update(GROUP_ADJACENCY.get(g, []))

    target_groups = adjacent_groups | used_groups
    query_tokens = expand_query(tokenize(task_text), task_text)

    candidates = []
    for skill in registry["skills"]:
        if skill["id"] in used_skill_ids:
            continue
        if skill.get("priority") == "duplicate":
            continue
        if skill["group"] in target_groups:
            sc, reasons = score_skill(skill, query_tokens, task_text)
            if sc > 0:
                rel = "same domain" if skill["group"] in used_groups else f"adjacent ({skill['group']})"
                candidates.append({
                    "id": skill["id"],
                    "group": skill["group"],
                    "description": skill.get("description", "")[:120],
                    "score": round(sc, 1),
                    "relation": rel,
                })

    candidates.sort(key=lambda x: -x["score"])
    return candidates[:5]


def format_post_task(recommendations, used_skills):
    lines = [f"Task completed using: {', '.join(used_skills)}", ""]
    lines.append("NEXT STEPS (related skills):")
    if recommendations:
        for i, r in enumerate(recommendations, 1):
            lines.append(f"  {i}. {r['id']} [{r['group']}] (score: {r['score']})")
            lines.append(f"     {r['description']}")
            lines.append(f"     relation: {r['relation']}")
    else:
        lines.append("  (no adjacent recommendations)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skill_router.py \"task description\"")
        print("       python skill_router.py --json \"task description\"")
        print("       python skill_router.py --post-task skill1,skill2 \"task description\"")
        sys.exit(1)

    json_mode = "--json" in sys.argv
    post_task_mode = "--post-task" in sys.argv

    if post_task_mode:
        args = [a for a in sys.argv[1:] if a not in ("--post-task", "--json")]
        if len(args) < 2:
            print("Usage: --post-task skill1,skill2 \"task description\"")
            sys.exit(1)
        used = args[0].split(",")
        task = " ".join(args[1:])
        recs = post_task_recommend(used, task)
        if json_mode:
            print(json.dumps(recs, indent=2, ensure_ascii=False))
        else:
            print(format_post_task(recs, used))
    else:
        query = " ".join(a for a in sys.argv[1:] if a not in ("--json",))
        result = route(query)
        if json_mode:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
