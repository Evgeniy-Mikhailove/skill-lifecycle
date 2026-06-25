# Getting Started

## Requirements

- Python 3.9 or later
- Claude Code installed (`~/.claude/` directory exists)
- Some skills already installed in `~/.claude/skills/`

## Installation

```bash
git clone https://github.com/Evgeniy-Mikhailove/skill-lifecycle.git
cd skill-lifecycle
python install.py
```

This copies all tools to `~/.claude/orchestration/`.

## First Run

### 1. Build your registry

Scan all existing skills on disk and generate `REGISTRY.json`:

```bash
python ~/.claude/orchestration/build_registry.py
```

This reads every `SKILL.md` file, extracts metadata from frontmatter, auto-assigns groups, and generates trigger keywords.

### 2. Try the router

```bash
python ~/.claude/orchestration/skill_router.py "build a REST API with authentication"
```

You'll see 5 direct matches and 5 potential next-step skills.

### 3. Run an audit

```bash
python ~/.claude/orchestration/audit.py
```

This checks: are all registered skills actually on disk? Are there orphan skills not in the registry? Any skills missing triggers?

## Daily Workflow

1. **Before a task** - run `skill_router.py "task description"` to find relevant skills
2. **After a task** - evaluate the outcome:
   - Worked as-is: `skill_usage.py log <skill> "<task>" success`
   - Needed adjustments: first `skill_evolve.py learn <skill> "<problem>" "<fix>"`, then `skill_usage.py log <skill> "<task>" adjusted`
   - Didn't help: first `skill_evolve.py learn <skill> "<problem>" "<alternative>"`, then `skill_usage.py log <skill> "<task>" failed`
3. **When installing a new skill** - run `skill_register.py <path>`
4. **Periodically** - run `audit.py` to catch orphans and consistency issues

**Key rule:** every `adjusted` or `failed` outcome must include a `skill_evolve.py learn` call. Without it, the experience from the session is lost.

## Configuration

By default, all paths are auto-detected from your `~/.claude/` directory. To override, create `~/.claude/orchestration/config.json`:

```json
{
  "registry_path": "/custom/path/REGISTRY.json",
  "index_path": "/custom/path/INDEX.md",
  "canvas_output": "/my/obsidian/vault/skill-map.canvas"
}
```

## Integrating with CLAUDE.md (CRITICAL STEP)

**Without CLAUDE.md configuration, skills will never adapt.** The scripts exist, but nothing tells the agent when to call them.

See the full setup guide: **[claude-md-setup.md](claude-md-setup.md)**

Quick version - add two blocks to your `~/.claude/CLAUDE.md`:
1. **Skill Auto-Routing** - tells the agent to find skills before each task
2. **Skill Adaptation** - tells the agent to record lessons after each task

This is what closes the feedback loop. Without it, you have tools but no behavior.
