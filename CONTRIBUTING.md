# Contributing to DOE Helper

Thank you for your interest in contributing to the Design of Experiments (DOE) Helper tool! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing. We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/MartinGallagher-code/design_of_experiments.git
   cd design_of_experiments
   ```

2. **Install in development mode with dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

   Pre-commit hooks run automatically on every commit and check for:
   - Trailing whitespace and line ending issues
   - YAML/TOML/JSON validity
   - Python syntax errors (compileall)
   - Code linting (ruff)

### Running Tests

Run the full test suite:
```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=doe --cov-report=html --cov-report=term-missing
```

Open `htmlcov/index.html` to view coverage details.

### Code Style

This project enforces code quality through:

- **Linting**: `ruff check doe tests` (also runs in pre-commit)
- **Type checking**: `mypy doe --strict` (Python 3.12 in CI, targeting `python_version = 3.9`)
- **Formatting**: Follow PEP 8; ruff auto-fixes many issues with `ruff check --fix`

The minimum supported runtime is Python 3.9, so every module in `doe/` that uses
PEP 604 unions (`str | None`) must start with `from __future__ import annotations`.
Without it those annotations are evaluated at import time and raise `TypeError` on
3.9. Avoid 3.10+ runtime features (`match` statements, `zip(..., strict=)`,
`itertools.pairwise`, `dataclass(slots=...)`) in library code.

Pre-commit hooks automatically run ruff on each commit. If a check fails:
1. Fix the issues locally
2. Stage the changes again
3. Commit

## Reporting Bugs

Found a bug? Please create an issue using the [bug report template](https://github.com/MartinGallagher-code/design_of_experiments/issues/new?template=bug_report.md).

Include:
- Your Python version and OS
- Steps to reproduce the issue
- Expected vs actual behavior
- A minimal reproducible example (if possible)
- Relevant output or error messages

## Suggesting Features

Have an idea? Please create an issue using the [feature request template](https://github.com/MartinGallagher-code/design_of_experiments/issues/new?template=feature_request.md).

Describe:
- The problem you're trying to solve
- Your proposed solution
- Alternative approaches you've considered
- Any additional context

## Pull Request Process

1. **Create a branch** from main using the naming convention `<type>/<description>`:
   ```bash
   git checkout -b fix/issue-title
   git checkout -b feature/new-capability
   git checkout -b docs/update-guides
   ```

2. **Make your changes** and commit with clear messages (see below)

3. **Push to your fork** and open a pull request against `main`

4. **Fill out the PR template** with:
   - Link to related issue(s)
   - Description of changes
   - Type of change (bug fix, feature, refactor, docs)
   - Testing performed
   - Confirmation that tests pass and coverage doesn't decrease

5. **Address review feedback** — maintainers will review and may request changes

6. **Merge** — Once approved, the PR will be merged to main

### Commit Message Conventions

Write clear, descriptive commit messages:

- **Prefix with a type**: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Use imperative mood**: "Add feature" not "Added feature"
- **Keep first line under 50 characters**
- **Add detailed explanation in body if needed**

Examples:
```
fix: handle empty response values in result parsing

Previously empty strings in JSON results would raise opaque
"could not convert string to float" errors. Now we provide
a file-pointing ValueError with context.

feat: add --filter-runs flag to exclude outliers from analysis

Closes #123

docs: add example of mixture design usage
```

## Development Workflow

### Making Changes

1. Create a branch for your work
2. Make changes and add tests
3. Run tests locally: `pytest tests/ -v`
4. Run code checks: `ruff check doe tests` and `mypy doe --strict`
5. Pre-commit hooks will run automatically on commit

### Testing Guidelines

- Add tests for any new functionality
- Maintain or improve code coverage
- Cover edge cases and error conditions
- Use descriptive test names

Example test:
```python
def test_load_config_with_missing_file():
    """Should raise FileNotFoundError for non-existent config."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.json")
```

### Documentation

- Update docstrings for public functions/classes
- Update [docs/](docs/) markdown files for user-facing changes
- Update [README.md](README.md) for major changes
- Update [CHANGELOG.md](CHANGELOG.md) in an `[Unreleased]` section

## Design Considerations

When adding new features or designs:

1. **Backward compatibility**: Don't break existing APIs without discussion
2. **Dependencies**: Minimize new external dependencies; lazy-import where possible
3. **Performance**: Test with larger designs (100+ factors)
4. **Error messages**: Provide actionable feedback to users
5. **Documentation**: Include examples and edge case notes

## Security

Found a security vulnerability? Please **do not** open a public issue. Instead, see [SECURITY.md](SECURITY.md) for responsible disclosure.

## Questions?

- Check existing [issues](https://github.com/MartinGallagher-code/design_of_experiments/issues) and [discussions](https://github.com/MartinGallagher-code/design_of_experiments/discussions)
- Open a [discussion](https://github.com/MartinGallagher-code/design_of_experiments/discussions) for questions
- Reach out to the maintainer

## License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0-or-later](LICENSE) license.

---

Thank you for contributing to DOE Helper! 🙏
