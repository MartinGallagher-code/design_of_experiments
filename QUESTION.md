# Production Readiness Questions

## Type Hints Enforcement (Issue #29)

**Question**: How strictly should we enforce type hints?

**Current situation**:
- Running mypy with strict mode reveals ~150+ type errors across the codebase
- Errors include: missing type annotations on ~80+ functions, missing generic type arguments, untyped calls, etc.
- Adding full strict type hints would require significant refactoring across most modules

**Options**:

1. **Full Strict Mode** (Current config)
   - Pros: Maximum type safety, excellent IDE support
   - Cons: Requires ~2-4 hours of refactoring
   - Scope: All 150+ errors must be fixed

2. **Moderate Type Checking** 
   - Pros: Good safety without massive refactor
   - Cons: Some type safety gaps remain
   - Config: Use default (not strict), disallow_untyped_defs for new code
   - Scope: Only fix critical/public API functions (~30-40 errors)

3. **Advisory Only (Current CI setup)**
   - Pros: No immediate blocking work
   - Cons: Type safety not enforced
   - Could enable `--ignore-without-error` flag to warn but not fail

**Recommendation**: Option 2 (Moderate) 
- Fix type hints for public APIs in models.py, config.py, design.py, analysis.py, rsm.py
- Add `# type: ignore` for complex internal functions where needed
- Enable strict checking on new code going forward
- Plan full migration for v0.4.0 or later

**What would you prefer?** Please update QUESTION.md with your choice or let me know which option to implement.
