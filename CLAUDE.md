# Notes for Claude

DOE Helper is a Python command-line tool for Design of Experiments: it builds
design matrices, generates runner scripts, and analyses the results (ANOVA,
response surfaces, optimisation, HTML reports). It is published on PyPI as
`doehelper`; the package is `doe` and the command is `doe`. `README.md` is the
front page, `docs/` is the manual (MkDocs, on Read the Docs), and
`CONTRIBUTING.md` says how a change is made.

## Checks

What `.github/workflows/ci.yml` runs on every pull request and every push to
`main` (the `test` job on Python 3.9-3.12, its repository-level gates on 3.12
only, and the `version` job):

```bash
python -m pip install --upgrade pip setuptools
pip install -e ".[dev]"
pip-audit --skip-editable
reuse lint
python -m compileall -q doe tests
ruff check doe tests
bandit -r doe --exit-zero
mypy doe
pytest tests/ -v --tb=short --cov=doe --cov-fail-under=100   # 3.10+; 3.9 runs it without the threshold
bash tests/check_version.sh origin/main                     # the version job
```

Read the Docs builds the manual from `mkdocs.yml` after a merge; to check it
first: `pip install -r docs/requirements.txt && mkdocs build --strict`.

## Every task is a ticket

Everything done here goes through a ticket in `MartinGallagher-code/shared_tools`,
which keeps every project's tickets as files and moves each one Backlog → In Progress
→ Review → Done (Adversarial Test only when the owner asks). Before any change:

1. Attach `MartinGallagher-code/shared_tools` with `add_repo` and push access, and
   clone it. If a clone is already here, pull it instead
   (`git -C <shared_tools clone> pull --ff-only`): a stale clone has a stale
   `CLAUDE.md` and a stale `ticket.py`.
2. Read the "Every task is a ticket" section of its `CLAUDE.md`. It sets out what each
   column requires, and none of it is optional.
3. Open the ticket with the shared_tools clone's script, not a path in this
   repository:

   ~~~bash
   <shared_tools clone>/scripts/ticket.py new <this repository's name> "Imperative title" --request "the request, in the user's own words"
   ~~~

**Every change moves the version**, however small: a pull request into `main` raises
it in every place it is written and opens `CHANGELOG.md` with that version's own
dated section, never an "Unreleased" heading left for later. CI fails a pull request
whose version is not greater than its base branch's. This file's own section on the
version says where it is written.

The board: https://claude.ai/artifact/HrB3RpVpqGGQS7UZgZsMJm

## Every change moves the version

The owner's rule (shared_tools BN-002): **whenever this project changes, its version
changes with it**, however small the change: code, tests, docs or CI. A pull request
into `main` carries its own bump and its own `CHANGELOG.md` section, never an
"Unreleased" heading left for later.

- Patch for fixes, docs, tests and CI; minor for anything new a user can use; major
  only when something that worked stops working the way it did.
- In the same pull request: `pyproject.toml`, `doe/__init__.py` and `CITATION.cff`
  (with its `date-released`), and a `## [X.Y.Z] — YYYY-MM-DD` section at the top of
  `CHANGELOG.md`. `tests/check_version.sh` fails if any of them disagree.
- The **version** job in CI fails a pull request whose version is not greater than its
  base branch's, and a push to `main` whose version is not greater than what `main` had
  before it. If `main` moves while a pull request is open, rebase and bump again.
- Dependabot's pull requests are not exempt: push a bump and a changelog section onto
  one before merging it.
- Publishing is a separate step, and a person's call: here that call is the merge.
  `.github/workflows/release.yml` runs on every push to `main` that touches
  `pyproject.toml` and, when the version has no tag yet, tags `vX.Y.Z`, creates the
  GitHub release from that version's `CHANGELOG.md` section and publishes to PyPI, so
  every pull request merged under this rule is published. Do not merge one unless it
  should be.
