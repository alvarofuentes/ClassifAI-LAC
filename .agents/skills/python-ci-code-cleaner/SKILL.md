---
name: python-ci-code-cleaner
description: >-
  Comprehensive guide and runbook for Python code cleaning, Ruff linting, Bandit security analysis,
  code formatting, and GitHub Actions CI compliance. Use this skill whenever writing, refactoring,
  cleaning code, or preparing commits/pushes to ensure 100% green CI builds.
---

# Python CI Code Cleaner & Quality Standard

This skill establishes the mandatory protocol for maintaining clean, secure, and compliant Python code in accordance with modern CI/CD pipelines (GitHub Actions, Ruff, Bandit, Pytest, UV).

---

## 🛡️ The 5-Gate CI Validation Checklist

Every agent making modifications to Python code must execute and verify the following 5 gates before committing or declaring work complete:

```text
[ Gate 1: Dependencies ]  uv lock --check
[ Gate 2: Linter ]        uv tool run ruff check .
[ Gate 3: Formatter ]     uv tool run ruff format --check .
[ Gate 4: Security ]      uv tool run bandit -r src
[ Gate 5: Unit Tests ]    uv run pytest
```

---

## 📋 Step-by-Step Execution Protocol

### Step 1: Lockfile Integrity
Verify that dependencies in `pyproject.toml` are properly resolved:
```bash
uv lock --check
```
*If failed:* Run `uv lock` to synchronize `uv.lock`.

---

### Step 2: Linter Standards (Ruff)
Run the linter check:
```bash
uv tool run ruff check .
```

#### Common Linter Rules & How to Resolve:
1. **`I001` (Unsorted/Unformatted Imports):**
   - Group imports: Standard library first, third-party libraries second, local application modules last.
   - Run `uv tool run ruff check . --fix` for automatic sorting.
2. **`E501` (Line Too Long > 120 chars):**
   - Wrap long docstrings, comments, list definitions, or function calls across multiple lines.
   - For string messages in loggers, use formatted parameters: `logging.info("Msg: %s", var)` instead of long f-strings.
3. **`D200` & `D417` (Google Docstrings):**
   - Single-line docstrings must fit on one line: `"""Summary line."""`
   - Multi-line docstrings must document all arguments listed in the function signature under `Args:`.
4. **`F841` (Unused Variables):**
   - Remove unused variables or prefix with `_` if intentionally ignored.
5. **`RUF005` (Iterable Unpacking):**
   - Use `["a", "b", *list_c]` instead of list concatenation `["a", "b"] + list_c`.
6. **Auxiliary / Scratch Scripts Isolation:**
   - Standalone experimental scripts (e.g. in `scripts/`, `scratch/`, `poc/`, `DEMO/`) must be listed in `extend-exclude` in `pyproject.toml` so they do not block the core library CI.

---

### Step 3: Code Formatting (Ruff Format)
Verify and apply code formatting:
```bash
# Check formatting
uv tool run ruff format --check .

# Auto-apply formatting
uv tool run ruff format .
```
- **Rule:** Never commit code that causes `ruff format --check .` to fail.

---

### Step 4: Security Scan (Bandit)
Run the static security analysis on the source code:
```bash
uv tool run bandit -r src
```

#### Security Guidelines:
1. **`B404` & `B603` (Subprocess Execution):**
   - Only execute controlled, internal subcommands with explicit argument lists (never `shell=True` on untrusted input).
   - Annotate explicitly with `# nosec B404` on the import and `# nosec B603` on the `subprocess.run(...)` line when reviewed and safe.
2. **`B904` (Exception Chaining):**
   - Always chain exceptions in `except` blocks using `raise CustomException(...) from e` or `from None` to preserve traceback context.
3. **No Hardcoded Secrets or Credentials:**
   - Load API keys and secrets strictly from environment variables or secure storage.

---

### Step 5: Unit Test Suite (Pytest)
Run the test suite to prevent regressions:
```bash
uv run pytest
```
- **Discovery Scope:** Ensure `[tool.pytest.ini_options]` in `pyproject.toml` specifies `testpaths = ["tests"]` to avoid running untracked or auxiliary test scripts outside the test suite.
- **Mocking & Determinism:** Unit tests must be fast, deterministic, and mock external API / disk dependencies where appropriate.

---

## ⚡ Quick One-Liner for Full Validation (PowerShell / Windows)

```powershell
uv lock --check; uv tool run ruff check .; uv tool run ruff format --check .; uv tool run bandit -r src; uv run pytest
```
*(All 5 checks must pass with exit code 0 before pushing).*
