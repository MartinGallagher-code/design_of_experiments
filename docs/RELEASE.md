# Release Process

This document describes how a new version of DOE Helper is made and released.

Every pull request moves the version, however small the change: code, tests,
docs or CI, and Dependabot's pull requests included. The bump and the
changelog section are part of the pull request, never left for a later
release. Merging the pull request is what publishes it.

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Breaking changes to the public API
- **MINOR** version (0.X.0): New backward-compatible features
- **PATCH** version (0.0.X): Bug fixes, docs, tests, CI and internal improvements

## Release Checklist

### 1. In every pull request

- [ ] Ensure all tests pass: `pytest tests/ -v --cov`
- [ ] Ensure type checking passes: `mypy doe --strict`
- [ ] Ensure linting passes: `ruff check doe tests`
- [ ] Ensure security checks pass: `bandit -r doe`
- [ ] Bump the version in `pyproject.toml`, `doe/__init__.py` and
      `CITATION.cff` (with its `date-released`)
- [ ] Add the new version's own section at the top of CHANGELOG.md
- [ ] `bash tests/check_version.sh origin/main` passes (CI's **version** job
      runs the same check)

```toml
[project]
version = "X.Y.Z"
```

Example CHANGELOG entry:
```markdown
## [X.Y.Z] — YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Deprecated features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes
```

There is no `[Unreleased]` section: each pull request's changes go under its
own version.

### 2. Merge, which publishes

Merging the pull request into `main` is the release. The
[Auto-release workflow](https://github.com/MartinGallagher-code/design_of_experiments/actions/workflows/release.yml)
(`.github/workflows/release.yml`) sees the new version in `pyproject.toml`,
creates the `vX.Y.Z` tag and the GitHub release from the CHANGELOG section,
and publishes to PyPI. Do not tag by hand. See [releasing.md](releasing.md).

### 3. Monitor the Release

- Watch the [Auto-release workflow](https://github.com/MartinGallagher-code/design_of_experiments/actions/workflows/release.yml)
- Confirm the package appears on [PyPI](https://pypi.org/project/doehelper/)
- Confirm the GitHub Release is created with SBOM artifacts

### 4. Post-Release

- [ ] Verify package installation: `pip install --upgrade doehelper`
- [ ] Test basic functionality
- [ ] Announce release on relevant channels

## Automated Release Process

The GitHub Actions workflow (`.github/workflows/release.yml`) automatically:

1. Creates the `vX.Y.Z` tag and the GitHub Release from CHANGELOG.md
2. Builds the package using `python -m build`
3. Generates SBOM in JSON and XML formats
4. Publishes to PyPI using trusted publishing (no credentials stored)
5. Uploads SBOM to the GitHub Release

## Version Numbering Decision Tree

```
Is this a breaking change to the public API?
  YES → MAJOR bump (e.g., 0.3.0 → 1.0.0)
  NO  → Does this add new functionality?
        YES → MINOR bump (e.g., 0.3.0 → 0.4.0)
        NO  → PATCH bump (e.g., 0.3.0 → 0.3.1)
```

## Public API Changes

For MAJOR version bumps involving breaking changes:

1. Document the breaking change in CHANGELOG.md
2. Provide a migration guide in the release notes
3. Include examples of how to update code
4. Consider a deprecation period in a prior release (if possible)

## Rollback

If a release is found to be broken:

1. Delete the tag locally and on GitHub:
   ```bash
   git tag -d vX.Y.Z
   git push origin --delete vX.Y.Z
   ```

2. Delete the release on GitHub (admin only)

3. Fix the issue and prepare a new release with an incremented PATCH version

4. Optionally, yank the broken version on PyPI (don't delete; marking as yanked is safer)

## Questions?

Contact the maintainer at martinjgallagher@icloud.com
