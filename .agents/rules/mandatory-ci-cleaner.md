# Mandatory CI & Code Quality Rule

All AI agents operating in this repository MUST follow the procedures outlined in the `python-ci-code-cleaner` skill (`.agents/skills/python-ci-code-cleaner/SKILL.md`).

Before declaring any coding task complete or pushing changes:
1. Ensure `uv tool run ruff check .` passes with 0 errors.
2. Ensure `uv tool run ruff format --check .` passes with 0 changes needed.
3. Ensure `uv tool run bandit -r src` passes with 0 security findings.
4. Ensure `uv run pytest` passes 100% of unit tests.
