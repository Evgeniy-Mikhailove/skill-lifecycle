# Changelog

## [1.3.0] - 2026-06-25

### Added
- `docs/claude-md-setup.md` - full setup guide for CLAUDE.md configuration with copy-paste blocks and real-world examples
- Mandatory skill adaptation pattern: LOG stage split into LOG+ADAPT with explicit rules for `adjusted` and `failed` outcomes
- README: expanded CLAUDE.md Integration section explaining why CLAUDE.md is required, not optional

### Changed
- `SKILL_LIFECYCLE_PROTOCOL.md`: Stage 4 (LOG) rewritten as LOG+ADAPT with a decision table for all three outcomes
- Stage 5 (EVOLVE) now explicitly states it requires CLAUDE.md config to work
- `docs/getting-started.md`: daily workflow updated with the full adaptation loop; CLAUDE.md section marked as critical step
- README Documentation section: `claude-md-setup.md` added as required reading

### Fixed
- Closed feedback loop gap: previously `skill_evolve.py` existed but nothing told the agent when to call it; now the protocol and CLAUDE.md template enforce this

## [1.2.0] - 2026-06-24

### Added
- 6-tier model routing: Haiku -> Gemini -> GPT Codex -> Sonnet -> Fable -> Opus
- Cross-provider support: Anthropic, OpenAI, Google in one routing table
- Task-to-model decision matrix with cost tiers
- Escalation policy with automatic tier progression
- Models badge in README

### Changed
- Router now suggests optimal model alongside skill matches
- README updated with model routing documentation

## [1.1.0] - 2026-06-20

### Added
- `.github/ISSUE_TEMPLATE/` — structured bug reports and feature requests
- `.github/FUNDING.yml` — sponsor button
- `docs/getting-started.md` — detailed setup guide
- `docs/architecture.md` — how the system works internally
- `CHANGELOG.md` — version history
- Before/After comparison in README
- Stars badge in README

### Changed
- README restructured with storytelling approach (problem-first, not feature-first)
- Discussions enabled on the repository

## [1.0.0] - 2026-06-20

### Added
- `skill_router.py` — find skills by task description (5 direct + 5 potential)
- `skill_register.py` — auto-categorize and register new skills
- `skill_usage.py` — track usage with success/adjusted/failed outcomes
- `skill_evolve.py` — record lessons learned, deprecate outdated approaches
- `audit.py` — health check for the skill ecosystem
- `build_registry.py` — rebuild REGISTRY.json from disk
- `build_canvas.py` — generate Obsidian visual map
- `install.py` — one-command installation
- `config.py` — path configuration
- Example skill with Lessons Learned section
- Lifecycle Protocol documentation
- Apache 2.0 license
