# Architecture

## How It Works

```
                    ┌─────────────────┐
                    │  REGISTRY.json  │  ← single source of truth
                    │  (all skills,   │
                    │   triggers,     │
                    │   groups)       │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
    │ skill_router │ │skill_register│ │    audit     │
    │              │ │              │ │              │
    │ task text    │ │ SKILL.md     │ │ disk scan    │
    │ → 5 direct   │ │ → auto-group │ │ → health     │
    │ → 5 potential│ │ → triggers   │ │   report     │
    │ → cyber hits │ │ → 3 files    │ │              │
    └──────────────┘ └──────────────┘ └──────────────┘
            │
    ┌───────▼──────┐ ┌──────────────┐
    │ skill_usage  │ │ skill_evolve │
    │              │ │              │
    │ log outcomes │ │ learn lesson │
    │ → usage.log  │ │ → SKILL.md   │
    │ → analytics  │ │ deprecate    │
    └──────────────┘ └──────────────┘
```

## Data Flow

### Registration
```
SKILL.md (on disk)
  → skill_register.py reads frontmatter
  → auto-determines group (14 categories)
  → generates trigger keywords from description + tags
  → writes to REGISTRY.json + INDEX.md + ROUTER_REGISTRY.md
```

### Routing
```
Task description (text)
  → tokenize + expand with synonym map
  → score each skill: trigger match (4x) + id match (2x) + desc match (1x)
  → apply priority weighting (primary > conditional > fallback)
  → sort by score
  → return top 5 DIRECT + top 5 POTENTIAL (adjacent groups)
  → optionally search cybersecurity package index.json
```

### Evolution
```
Problem + Solution (from real usage)
  → skill_evolve.py appends to SKILL.md
  → ## Lessons Learned section grows over time
  → next user of the skill sees known pitfalls
  → outdated approaches get ## Deprecated Approaches section
```

## File Responsibilities

| File | Reads | Writes | Purpose |
|------|-------|--------|---------|
| `REGISTRY.json` | all tools | `build_registry`, `skill_register` | Central truth |
| `INDEX.md` | `audit` | `skill_register` | Human-readable list |
| `ROUTER_REGISTRY.md` | humans | `skill_register` | Categorized routing table |
| `usage.log` | `skill_usage` | `skill_usage` | JSONL usage log |
| `evolution.log` | `skill_evolve` | `skill_evolve` | JSONL evolution history |
| `SKILL.md` (per skill) | `skill_router`, `skill_register` | `skill_evolve` | Skill definition |

## Group Adjacency

The router uses a graph of related groups to suggest "potential" skills from neighboring domains:

```
content-marketing ←→ design-media ←→ coding-dev
       ↕                                  ↕
research-analytics ←→ ai-ml-agents ←→ automation-api
                           ↕               ↕
                   orchestration-meta  devops-cicd
                                          ↕
               review-debug-security ←→ cybersecurity
                       ↕
                  code-quality
```

When you use a `coding-dev` skill, the router suggests skills from `code-quality`, `review-debug-security`, `devops-cicd`, and `automation-api` as potential next steps.
