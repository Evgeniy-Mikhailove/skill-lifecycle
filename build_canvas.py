#!/usr/bin/env python3
"""
Build Canvas -- generate an Obsidian .canvas map of the skill ecosystem.

Reads REGISTRY.json and produces a JSON Canvas file where each group
is a color-coded node containing its skills, with edges drawn between
adjacent groups.

Usage:
  python build_canvas.py
  python build_canvas.py --output /custom/path/skill-ecosystem.canvas
"""

import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from config import REGISTRY_PATH, CANVAS_OUTPUT


# ---------------------------------------------------------------------------
# Visual mapping tables
# ---------------------------------------------------------------------------

GROUP_COLORS = {
    "content-marketing": "1",
    "design-media": "2",
    "automation-api": "3",
    "coding-dev": "4",
    "review-debug-security": "5",
    "planning-management": "6",
    "files-documents": "1",
    "ai-ml-agents": "3",
    "research-analytics": "4",
    "obsidian-knowledge": "5",
    "code-quality": "6",
    "orchestration-meta": "2",
    "devops-cicd": "4",
    "cybersecurity": "5",
}

GROUP_NAMES = {
    "content-marketing": "Content / Marketing",
    "design-media": "Design / Media",
    "automation-api": "Automation / API",
    "coding-dev": "Coding / Dev",
    "review-debug-security": "Review / Security",
    "planning-management": "Planning",
    "files-documents": "Files / Docs",
    "ai-ml-agents": "AI / ML / Agents",
    "research-analytics": "Research / Analytics",
    "obsidian-knowledge": "Obsidian / KB",
    "code-quality": "Code Quality",
    "orchestration-meta": "Orchestration",
    "devops-cicd": "DevOps / CI/CD",
    "cybersecurity": "Cybersecurity",
}

ADJACENCY = {
    "content-marketing": ["design-media", "research-analytics", "ai-ml-agents"],
    "design-media": ["content-marketing", "coding-dev"],
    "automation-api": ["coding-dev", "devops-cicd", "ai-ml-agents"],
    "coding-dev": ["code-quality", "review-debug-security", "devops-cicd", "automation-api"],
    "review-debug-security": ["coding-dev", "code-quality", "cybersecurity"],
    "planning-management": ["orchestration-meta", "research-analytics"],
    "files-documents": ["automation-api", "obsidian-knowledge"],
    "ai-ml-agents": ["coding-dev", "automation-api", "research-analytics", "orchestration-meta"],
    "research-analytics": ["ai-ml-agents", "content-marketing"],
    "obsidian-knowledge": ["files-documents", "orchestration-meta"],
    "code-quality": ["coding-dev", "review-debug-security", "devops-cicd"],
    "orchestration-meta": ["ai-ml-agents", "automation-api"],
    "devops-cicd": ["coding-dev", "automation-api"],
    "cybersecurity": ["review-debug-security", "devops-cicd"],
}


# ---------------------------------------------------------------------------
# Canvas builder
# ---------------------------------------------------------------------------

def build(output_path=None):
    """Generate the .canvas file from the registry."""
    output = Path(output_path) if output_path else CANVAS_OUTPUT

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    skills_by_group = {}
    for s in registry["skills"]:
        g = s.get("group", "unknown")
        if g not in skills_by_group:
            skills_by_group[g] = []
        skills_by_group[g].append(s)

    nodes = []
    edges = []
    group_positions = {}

    cols = 4
    col_w = 420
    row_h = 500
    pad = 40

    groups_list = list(GROUP_NAMES.keys())
    for idx, group_id in enumerate(groups_list):
        col = idx % cols
        row = idx // cols
        x = col * (col_w + pad)
        y = row * (row_h + pad)
        group_positions[group_id] = (x, y)

        skills = skills_by_group.get(group_id, [])
        name = GROUP_NAMES.get(group_id, group_id)
        count = len(skills)
        color = GROUP_COLORS.get(group_id, "1")

        primary = [s for s in skills if s.get("priority") == "primary"]
        conditional = [s for s in skills if s.get("priority") == "conditional"]
        dup = [s for s in skills if s.get("priority") == "duplicate"]

        lines = [f"## {name} ({count})"]
        if primary:
            lines.append(f"**Primary ({len(primary)}):** " + ", ".join(s["id"] for s in primary[:6]))
            if len(primary) > 6:
                lines.append(f"  +{len(primary) - 6} more")
        if conditional:
            lines.append(f"**Optional ({len(conditional)}):** " + ", ".join(s["id"] for s in conditional[:6]))
            if len(conditional) > 6:
                lines.append(f"  +{len(conditional) - 6} more")
        if dup:
            lines.append(f"~~Duplicates: {', '.join(s['id'] for s in dup)}~~")

        text_content = "\n".join(lines)

        node = {
            "id": group_id,
            "type": "text",
            "x": x,
            "y": y,
            "width": col_w,
            "height": max(200, 80 + count * 8),
            "color": color,
            "text": text_content,
        }
        nodes.append(node)

    # Edges between adjacent groups (deduplicated)
    seen_edges = set()
    for group_id, adj_list in ADJACENCY.items():
        for adj in adj_list:
            edge_key = tuple(sorted([group_id, adj]))
            if edge_key not in seen_edges and adj in group_positions:
                seen_edges.add(edge_key)
                edges.append({
                    "id": f"edge-{group_id}-{adj}",
                    "fromNode": group_id,
                    "toNode": adj,
                    "fromSide": "right" if group_positions[group_id][0] < group_positions[adj][0] else "left",
                    "toSide": "left" if group_positions[group_id][0] < group_positions[adj][0] else "right",
                })

    # Package summary nodes
    for pkg in registry.get("packages", []):
        pkg_node = {
            "id": f"pkg-{pkg['id']}",
            "type": "text",
            "x": 0,
            "y": (len(groups_list) // cols + 1) * (row_h + pad),
            "width": cols * (col_w + pad) - pad,
            "height": 150,
            "color": "5",
            "text": (
                f"## {pkg['id']} ({pkg.get('total_skills', '?')} skills)\n"
                f"{pkg.get('description', '')[:200]}\n\n"
                f"**Subdomains:** "
                + ", ".join(
                    f"{sd['name']} ({sd['count']})"
                    for sd in sorted(pkg.get("subdomains", []), key=lambda x: -x["count"])[:10]
                )
            ),
        }
        nodes.append(pkg_node)

    # Stats summary node
    stats_node = {
        "id": "stats",
        "type": "text",
        "x": (cols - 1) * (col_w + pad),
        "y": -200,
        "width": col_w,
        "height": 160,
        "color": "6",
        "text": (
            f"## Skill Ecosystem\n"
            f"**Individual:** {registry['total_individual_skills']}\n"
            f"**Packages:** {registry['total_with_packages'] - registry['total_individual_skills']}\n"
            f"**Total:** {registry['total_with_packages']}\n"
            f"**Groups:** {len(groups_list)}\n"
            f"**Updated:** {registry['updated']}"
        ),
    }
    nodes.append(stats_node)

    canvas = {"nodes": nodes, "edges": edges}

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(canvas, f, indent=2, ensure_ascii=False)

    print(f"Canvas built: {output}")
    print(f"  {len(nodes)} nodes, {len(edges)} edges")
    print(f"  {registry['total_individual_skills']} individual + {registry['total_with_packages'] - registry['total_individual_skills']} in packages")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    custom_output = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            custom_output = sys.argv[idx + 1]

    build(output_path=custom_output)
