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

1. **Before a task** — run `skill_router.py "task description"` to find relevant skills
2. **After a task** — run `skill_usage.py log <skill> "<task>" success|adjusted|failed`
3. **When you find a workaround** — run `skill_evolve.py learn <skill> "<problem>" "<solution>"`
4. **When installing a new skill** — run `skill_register.py <path>`
5. **Periodically** — run `audit.py` to catch orphans and consistency issues

## Configuration

By default, all paths are auto-detected from your `~/.claude/` directory. To override, create `~/.claude/orchestration/config.json`:

```json
{
  "registry_path": "/custom/path/REGISTRY.json",
  "index_path": "/custom/path/INDEX.md",
  "canvas_output": "/my/obsidian/vault/skill-map.canvas"
}
```

## Integrating with CLAUDE.md

Add this to your global `~/.claude/CLAUDE.md`:

```markdown
## Skill Auto-Routing

For every non-trivial task:
1. Run `python ~/.claude/orchestration/skill_router.py "<task description>"`
2. Apply DIRECT results silently
3. Keep POTENTIAL results in mind for the next step
```

This makes your AI agent automatically search for relevant skills on every task.
