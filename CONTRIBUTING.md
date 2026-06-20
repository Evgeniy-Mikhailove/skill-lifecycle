# Contributing

Thanks for your interest in Skill Lifecycle Manager. Here's how to contribute.

## Ways to Help

- **Report bugs** — Open an issue with steps to reproduce
- **Suggest features** — Describe the problem you're solving, not just the solution
- **Improve docs** — Fix typos, add examples, clarify confusing sections
- **Add synonym pairs** — Expand the bilingual keyword map in `skill_router.py`
- **Share your setup** — Show how you organize 100+ skills in a discussion post

## Pull Requests

1. Fork the repo
2. Create a branch (`git checkout -b fix/router-scoring`)
3. Make your changes
4. Test with your own skill library
5. Open a PR with a clear description of what changed and why

## Code Style

- Python 3.9+ compatible
- No external dependencies
- UTF-8 everywhere (Windows compatibility matters)
- Docstrings on public functions
- Keep it simple — these are CLI tools, not a framework

## Security

Never commit files containing API keys, tokens, personal paths, or credentials. The `.gitignore` excludes `config.json`, `.env`, and log files for this reason.

If you find a security issue, please email instead of opening a public issue.
