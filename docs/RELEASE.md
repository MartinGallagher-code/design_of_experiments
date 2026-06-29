# Release Process

This document describes how to release a new version of DOE Helper.

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Breaking changes to the public API
- **MINOR** version (0.X.0): New backward-compatible features
- **PATCH** version (0.0.X): Bug fixes and internal improvements

## Release Checklist

### 1. Prepare the Release

- [ ] Ensure all tests pass: `pytest tests/ -v --cov`
- [ ] Ensure type checking passes: `mypy doe --strict`
- [ ] Ensure linting passes: `ruff check doe tests`
- [ ] Ensure security checks pass: `bandit -r doe`
- [ ] Review CHANGELOG.md for completeness
- [ ] Create or update the entry for the new version in CHANGELOG.md

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

### 2. Update Version

Update the version in `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

Commit this change:
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.X.Z"
```

### 3. Create Git Tag

Create a signed (or unsigned) tag:

```bash
# Unsigned tag (simple)
git tag vX.Y.Z

# Or signed tag (recommended)
git tag -s -m "Release X.Y.Z" vX.Y.Z
```

### 4. Push to Repository

```bash
git push origin main
git push origin vX.Y.Z
```

This will trigger the GitHub Actions publish workflow.

### 5. Monitor the Release

- Watch the [publish workflow](https://github.com/MartinGallagher-code/design_of_experiments/actions/workflows/publish.yml)
- Confirm the package appears on [PyPI](https://pypi.org/project/doehelper/)
- Confirm the GitHub Release is created with SBOM artifacts

### 6. Post-Release

- [ ] Verify package installation: `pip install --upgrade doehelper`
- [ ] Test basic functionality
- [ ] Announce release on relevant channels
- [ ] Update version in CHANGELOG.md with `[Unreleased]` section for next development cycle

Example:
```markdown
## [Unreleased]

### Added
(None yet)

## [X.Y.Z] — YYYY-MM-DD
...
```

## Automated Release Process

The GitHub Actions workflow (`.github/workflows/publish.yml`) automatically:

1. Builds the package using `python -m build`
2. Generates SBOM in JSON and XML formats
3. Publishes to PyPI using trusted publishing (no credentials stored)
4. Uploads SBOM to the GitHub Release

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
