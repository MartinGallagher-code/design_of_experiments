# Releasing

Every pull request moves the version, however small the change (code, tests,
docs or CI). In the same pull request:

1. Bump the version in `pyproject.toml`, `doe/__init__.py` and `CITATION.cff`
   (with its `date-released`).
2. Add a `## [X.Y.Z] — YYYY-MM-DD` entry at the top of `CHANGELOG.md` with
   the user-visible changes. There is no `[Unreleased]` section.
3. Run `bash tests/check_version.sh origin/main`: it fails if the three
   places disagree, the changelog does not open with that version, or the
   version is not greater than `main`'s. CI's **version** job runs the same
   check on every pull request.

Publishing is the merge. The pipeline is fully automated, so merging a pull
request publishes its version. Once the merge lands on `main`:

* **`release.yml`** notices `pyproject.toml` changed, parses out the
  new version, extracts the matching `## X.Y.Z` section from
  `CHANGELOG.md`, and creates a GitHub release at tag `vX.Y.Z`.
* Its **`publish`** job then builds the wheel + sdist, uploads them to PyPI
  via the `pypi` environment, and attaches an SBOM to the release.

Both jobs are idempotent: re-running them after a release already exists is
a no-op.

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
  `tests/check_version.sh` fails such a pull request before it gets there.
- Tag already exists on origin → workflow exits cleanly without
  attempting to recreate it.
