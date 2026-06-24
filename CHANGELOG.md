# Changelog

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
