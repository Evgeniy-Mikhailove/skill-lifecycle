# CLAUDE.md Setup Guide

How to configure your CLAUDE.md so that skills learn from every session.

## Why this matters

The Skill Lifecycle Manager includes `skill_evolve.py` - a script that records lessons learned directly into SKILL.md files. But scripts don't run themselves. Your AI agent needs explicit instructions in CLAUDE.md that tell it **when** to call the evolve script.

Without this setup:
- Skills get used, but never improved
- You find a workaround for a skill's limitation, but next session starts from zero
- The same problems get solved over and over

With this setup:
- Every session that uses a skill can improve it
- Workarounds, fixes, and discoveries are recorded in SKILL.md
- Future sessions (yours or anyone else's) see the accumulated experience

## Setup

Add the following blocks to your `~/.claude/CLAUDE.md` (global) or your project's `CLAUDE.md`.

### Block 1: Skill Routing

This tells the agent to find the right skill for each task.

```markdown
## Skill Auto-Routing (REQUIRED)

For every non-trivial task:

1. Run `python ~/.claude/orchestration/skill_router.py "<task description>"`
2. From DIRECT results - apply top skills silently (read their SKILL.md, follow the methodology)
3. POTENTIAL results - keep in mind for the next step
4. After the task - evaluate and log the outcome (see Skill Adaptation below)

Skills should not be announced. Just follow their methodology.
```

### Block 2: Skill Adaptation (the critical part)

This is what makes skills learn. Without this block, the lifecycle is incomplete.

```markdown
## Skill Adaptation (MANDATORY pattern)

After EVERY skill application, evaluate the result and act:

1. Skill worked as-is -> `skill_usage.py log <id> "<task>" success` (silently)
2. Skill needed adjustments during work -> FIRST `skill_evolve.py learn <id> "<what didn't work>" "<what we did instead>"`, THEN `skill_usage.py log <id> "<task>" adjusted`
3. Skill didn't help, found a different approach -> FIRST `skill_evolve.py learn <id> "<problem>" "<alternative approach>"`, THEN `skill_usage.py log <id> "<task>" failed`

Triggers that REQUIRE writing to the skill:
- An approach from the skill did not work and a different solution was found
- An additional step was discovered that strengthens the skill
- A limitation was found that the skill does not warn about
- An API/library/tool referenced in the skill has changed
- A workaround was needed that future users should know about

This is NOT optional. Every adjusted/failed outcome without an evolve learn call = lost experience. The whole point of the lifecycle is that skills grow smarter with each use.

When an approach becomes outdated:
skill_evolve.py deprecate <skill_id> "<what>" "<replacement>"
```

### Block 3: Lifecycle Commands (reference)

```markdown
## Skill Lifecycle Commands

- Install new skill: `python ~/.claude/orchestration/skill_register.py <path-to-skill>`
- Post-task recommendations: `python ~/.claude/orchestration/skill_router.py --post-task skill1,skill2 "<what was done>"`
- Health check: `python ~/.claude/orchestration/audit.py`
- Evolution history: `python ~/.claude/orchestration/skill_evolve.py history [skill_id]`
- Find stale skills: `python ~/.claude/orchestration/skill_evolve.py stale 90`
- Usage report: `python ~/.claude/orchestration/skill_usage.py report`
```

## How it works in practice

### Example: skill works fine

You ask the agent to set up CI/CD. The router finds `ci-cd-automation`. The agent reads the SKILL.md, follows the steps, everything works.

Result: `skill_usage.py log ci-cd-automation "GitHub Actions setup" success`

Nothing gets written to the skill - it worked as documented.

### Example: skill needs adjustment

You ask the agent to build a Telegram bot. The router finds `telegram-bot-builder`. The agent follows the steps, but discovers that the polling approach from the skill causes timeouts on Railway. It switches to webhooks and the bot works.

Result:
```bash
skill_evolve.py learn telegram-bot-builder \
  "Polling approach causes timeouts on Railway free tier" \
  "Use webhooks instead of polling when deploying to Railway - set WEBHOOK_URL env var"

skill_usage.py log telegram-bot-builder "sales bot for Railway" adjusted
```

Now the SKILL.md contains this lesson. Next time anyone deploys to Railway using this skill, they see the webhook approach right away.

### Example: skill doesn't help

You ask the agent to optimize database queries. The router finds `sql-pro`. The agent reads the skill, but the actual problem turns out to be N+1 queries in the ORM layer, not raw SQL. The skill's approach doesn't apply.

Result:
```bash
skill_evolve.py learn sql-pro \
  "Skill focuses on raw SQL optimization but doesn't cover ORM N+1 detection" \
  "For ORM-level issues, check query logs for repeated patterns first, use EXPLAIN on the generated SQL"

skill_usage.py log sql-pro "ORM N+1 optimization" failed
```

The skill now warns future users about this limitation and provides a starting point for ORM issues.

## Verification

After setup, verify the lifecycle is working:

1. Run `python ~/.claude/orchestration/audit.py` - should show no warnings
2. Use a skill on a real task
3. Check the skill's SKILL.md - if the outcome was `adjusted` or `failed`, there should be a new entry under `## Lessons Learned`
4. Run `python ~/.claude/orchestration/skill_usage.py report` - should show the logged entry

## Multi-agent setup

If multiple AI agents share the same skill directory:
- Each agent needs the same CLAUDE.md blocks
- All agents write to the same SKILL.md files
- Lessons from one agent benefit all others
- Each agent can maintain its own `usage.log` (configure via `config.json`)
