# Production Readiness Questions

## Type Hints Enforcement (Issue #29) — BLOCKED

**Question**: How strictly should we enforce type hints?

**Current situation**:
- Running mypy with strict mode reveals ~150+ type errors across the codebase
- Errors include: missing type annotations on ~80+ functions, missing generic type arguments, untyped calls, etc.
- Adding full strict type hints would require significant refactoring across most modules
- mypy configuration added to pyproject.toml but not yet enforced in CI

**Options**:

1. **Full Strict Mode** (Current config in pyproject.toml)
   - Pros: Maximum type safety, excellent IDE support
   - Cons: Requires ~2-4 hours of refactoring
   - Scope: All 150+ errors must be fixed

2. **Moderate Type Checking** (RECOMMENDED)
   - Pros: Good safety without massive refactor
   - Cons: Some type safety gaps remain
   - Config: Use default (not strict), disallow_untyped_defs for new code only
   - Scope: Only fix critical/public API functions (~30-40 errors)

3. **Advisory Only** 
   - Pros: No immediate blocking work
   - Cons: Type safety not enforced
   - CI would warn but not fail

**Recommendation**: Option 2 (Moderate) 
- Fix type hints for public APIs in models.py, config.py, design.py, analysis.py, rsm.py
- Add `# type: ignore` for complex internal functions where needed
- Enable strict checking on new code going forward
- Plan full migration for v0.4.0 or later

**ACTION NEEDED**: Please choose an option (1, 2, or 3) so work on #29 can proceed.

---

## Summary of Completed Issues

✅ **Complete** (10 issues):
- #23: CONTRIBUTING.md
- #24: SECURITY.md
- #25: CODE_OF_CONDUCT.md
- #26: GitHub issue templates
- #27: GitHub pull request template
- #28: CHANGELOG.md (Keep a Changelog format)
- #30: Test coverage enforcement (80% minimum)
- #31: Integration tests (7 end-to-end tests)
- #32: Dependency security scanning (pip-audit)
- #33: SBOM generation (CycloneDX)
- #34: Release documentation (docs/RELEASE.md)
- #35: Public API documentation (docs/api.md)
- #36: REUSE compliance check
- #37: Static analysis (bandit)
- #38: README badges and links
- #39: ROADMAP.md

⏳ **Blocked** (1 issue):
- #29: Type hints enforcement — awaiting user guidance on Option 1/2/3
