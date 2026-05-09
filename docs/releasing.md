# Releasing

The release pipeline is fully automated. To cut a new version:

1. Bump the version in `pyproject.toml` and `doe/__init__.py`.
2. Add a `## X.Y.Z — YYYY-MM-DD` entry at the top of `CHANGELOG.md` with
   the user-visible changes.
3. Open a PR and merge it.

That's it. Once the merge lands on `main`:

* **`release.yml`** notices `pyproject.toml` changed, parses out the
  new version, extracts the matching `## X.Y.Z` section from
  `CHANGELOG.md`, and creates a GitHub release at tag `vX.Y.Z`.
* **`publish.yml`** is triggered by the `release: published` event,
  builds the wheel + sdist, and uploads to PyPI via the `pypi`
  environment.

Both workflows are idempotent: re-running them after a release already
exists is a no-op.

## Manual override

If you need to publish a release for a version that was bumped earlier
without firing the workflow, run **Auto-release** from the Actions tab
via *Run workflow*. It re-reads the version from `pyproject.toml` and
creates the missing release.

## CHANGELOG section discovery

`release.yml` uses an `awk` block to pull everything between
`## <ver>` and the next `## ` into the release notes. The tag and
release name are `vX.Y.Z` (with the leading `v`).

Edge cases:

- Missing CHANGELOG entry for the new version → release notes fall
  back to a placeholder ("No CHANGELOG entry found for X.Y.Z").
- Tag already exists on origin → workflow exits cleanly without
  attempting to recreate it.
