# AI Agent Guidelines & Mandatory Rules

## 🚨 MANDATORY RULE: Code Quality & CI/CD Compliance

All AI agents working on this codebase **MUST ALWAYS** comply with the code cleaning, security, and quality standard defined in the [`python-ci-code-cleaner`](./.agents/skills/python-ci-code-cleaner/SKILL.md) skill.

### Required Actions Before Proposing Commits or Pushes:
Whenever Python code is written, modified, or refactored, the agent **MUST** execute the 5-Gate CI Validation:

1. **Dependencies:** `uv lock --check` (Zero resolution errors).
2. **Linter (Ruff):** `uv tool run ruff check .` (Zero errors).
3. **Formatter (Ruff):** `uv tool run ruff format --check .` (Zero differences).
4. **Security (Bandit):** `uv tool run bandit -r src` (Zero vulnerabilities, use `# nosec` with explanation when safe).
5. **Unit Tests (Pytest):** `uv run pytest` (100% test pass rate).

### Coding Standards:
- **Line Length:** Maximum 120 characters across all docstrings, comments, and code.
- **Imports:** Sorted and grouped (standard library, third-party, local).
- **Exceptions:** Always chain exceptions in `except` blocks using `raise ... from e`.
- **Security:** Do not use `shell=True` or expose untrusted input to subcommands.
- **Isolation:** Auxiliary experimental scripts must remain isolated in `scripts/`, `scratch/`, or `poc/` and registered in `extend-exclude` in `pyproject.toml`.
