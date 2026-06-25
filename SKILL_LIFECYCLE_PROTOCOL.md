# Skill Lifecycle Protocol

Standard operating procedure for managing Claude Code skills at scale.

## The 7 Stages

### 1. INSTALL
Register every new skill with `skill_register.py`. One command writes to three files — REGISTRY.json, INDEX.md, and ROUTER_REGISTRY.md. No manual categorization needed.

### 2. ROUTE
Before non-trivial work, run `skill_router.py "<task>"`. It returns 5 direct matches and 5 potential next-step skills. Apply the direct matches, keep the potential ones in mind.

### 3. APPLY
Use the skill methodology. Don't announce which skill you're using — just follow its steps.

### 4. LOG + ADAPT (mandatory, not optional)
After applying a skill, evaluate the outcome and act accordingly:

| Outcome | What happened | Action |
|---------|--------------|--------|
| `success` | Skill worked as documented | `skill_usage.py log <id> "<task>" success` |
| `adjusted` | Skill needed changes to work | **First** `skill_evolve.py learn <id> "<problem>" "<solution>"`, **then** `skill_usage.py log <id> "<task>" adjusted` |
| `failed` | Skill didn't help, used different approach | **First** `skill_evolve.py learn <id> "<problem>" "<alternative>"`, **then** `skill_usage.py log <id> "<task>" failed` |

**Critical rule:** every `adjusted` or `failed` outcome MUST include a `skill_evolve.py learn` call before logging. An outcome without a lesson = lost experience.

Triggers that require writing to the skill:
- An approach from the skill did not work and a different solution was found
- An additional step was discovered that strengthens the skill
- A limitation was found that the skill does not warn about
- An API/library/tool referenced in the skill has changed
- A workaround was needed that future users should know about

### 5. EVOLVE
Lessons accumulate in each skill's SKILL.md under `## Lessons Learned`. Outdated approaches get marked with `skill_evolve.py deprecate`. Skills grow smarter with every session.

**Important:** This stage does not work automatically. The AI agent must be instructed to perform it via CLAUDE.md. See [docs/claude-md-setup.md](docs/claude-md-setup.md) for the required CLAUDE.md configuration.

### 6. RECOMMEND
After completing complex work, run `skill_router.py --post-task` to see what adjacent skills could improve or extend the result.

### 7. AUDIT
Periodically run `audit.py` to find orphan skills, missing triggers, stale files, and consistency issues.

## Key Principles

1. **No invisible skills.** Every skill must be registered and categorized.
2. **No lost experience.** Every workaround goes into the skill's Lessons Learned.
3. **No stale skills.** Outdated approaches get deprecated, not silently ignored.
4. **Data-driven cleanup.** Usage tracking shows what's valuable and what's dead weight.

## Multi-Agent Coordination

If multiple AI agents share skills:
- All agents read from the same REGISTRY.json
- Lessons Learned in SKILL.md are shared — any agent's fix benefits all
- Each agent maintains its own usage log
- The latest lesson always wins — they stack, don't conflict

## SKILL.md Format

```yaml
---
name: my-skill-id
description: What this skill does in one sentence
domain: development
subdomain: testing
tags:
- keyword1
- keyword2
version: '1.0'
---

# Skill Title

## Overview
What this skill is about.

## When to Use
When to apply this skill.

## Steps
1. First step
2. Second step

## Lessons Learned
### [YYYY-MM-DD] Problem title
**Problem:** What went wrong
**Solution:** What fixed it

## Deprecated Approaches
### [YYYY-MM-DD] DEPRECATED: Old approach
**Was:** What was used before
**Use instead:** What to use now
```
