# Changelog

## 0.3.0 — 2026-05-09

### Bootstrap & scaffolding
- `doe scaffold-config`, `doe scaffold-test` — annotated starter files.
- `doe init --factors --budget --goal [--with-test]` — bootstrap a working config (and optionally `test.py`) from a one-line description.
- `doe suggest` — print a recommended operation + run count + adaptive strategy without committing.

### Design generation
- `split_plot` operation with role-based whole-plot / subplot factors and within-plot randomisation.
- `--resolution N` knob on `fractional_factorial` (bumps run count until the requested resolution is achievable). Lex tie-break in the candidate-set search lifts the auto path: 2^(4-1) is now Resolution IV by default.
- `--replicate-center N` (also `settings.replicate_center`) appends N centre-point runs per block.
- `Factor.dtype: "int"` is now respected by every optimiser (rounded + clamped to the level range).
- `Factor.role: "whole_plot"` for split-plot designs.
- Constraint expressions (`"constraints": ["x + y <= 1.5", ...]`) parsed via an AST allow-list.
- Runner formats: `--format sh|py`, `--parallel N` (thread pool), `--executor slurm` with `--slurm-{partition,time,cpus-per-task,mem,max-concurrent}`.
- `--session [PREFIX]` writes each runner invocation to `<out>/<PREFIX>-<TIMESTAMP>/` and updates `<out>/latest`.
- D-optimal candidate set now includes a midpoint per 2-level continuous factor for richer coordinate exchange.
- `doe augment --type d_optimal` grows an existing design by N runs that maximise pooled `det(X'X)`.

### Running
- `doe simulate --func module:fn` drives the design directly from a Python function — no shell.
- Block-aware skip-existing semantics in every runner template.

### Analysis
- ANOVA path automatically selected from five options: pooled / replicates (block-aware grouping) / Lenth's PSE / split-plot two-error / blocked.
- **Model adequacy**: PRESS, predicted R², Shapiro-Wilk, Durbin-Watson, run-order drift slope+p, max leverage, max Cook's distance with `F(0.5, p, n-p)` cutoff.
- **Stationary point** classification from Hessian eigenvalues (maximum / minimum / saddle / ridge / rising_ridge), decoded into natural factor units.
- **Achieved power** retrospective from the actual residual MS — per-factor power and minimum detectable effect.
- **Cross-validation**: k-fold predicted-vs-actual with RMSE / MAE / R²<sub>cv</sub> (`--cv-folds K`, default `min(n, 5)`).
- **Alias structure** for fractional factorial / Plackett-Burman, with resolution detection.
- **Scheffé canonical form** for mixture designs.
- **Sobol sensitivity** (`doe sensitivity`) — first-order and total-order indices on the fitted surrogate, with HTML stacked-bar charts (`--html`).
- `--no-rsm` skips the RSM refit and the model-adequacy / stationary-point / cross-validation sections (for big designs).
- HTML report sticky table-of-contents.

### Optimisation & iteration
- Six adaptive strategies: `refine`, `explore`, `balanced`, `model_guided` (RSM optimum + max-leverage), `bayesian` (numpy-only Gaussian process + Expected Improvement, q-EI via constant-liar fantasising, mixed numeric + one-hot categorical encoder, heteroscedastic noise from replicate scatter), `multi_objective` (per-response GPs + random Tchebycheff scalarisation).
- `doe calibrate` fits free parameters in a parametric simulator to observed data via L-BFGS-B.
- Adaptive state lives at `cfg.out_directory` (survives `--session` switches); `--state-name FOO` for trajectory branching.

### Comparing & reporting
- `doe compare --baseline DIR --candidate DIR` — paired-run delta + Cohen's d, per-factor effect delta with sign-flip flag, intercept-shift vs slope-shift decomposition. HTML embeds per-run delta dotplot.
- `doe trend --sessions DIR1 DIR2 …` — multi-session regression with intercept / slope drift per session step. HTML embeds per-session-mean line plot with drift overlay.
- `doe archive` — bundle a session into a tarball with a SHA-256 manifest.
- `doe serve --root results/` — stdlib HTTP localhost browser for sessions.

### Documentation
- `docs/user_guide.md`, `docs/commands.md`, `docs/strategies.md`, `docs/config.md`, `docs/cookbook.md`.
- README rewritten around the bootstrap path; Documentation block at the top.

### Other
- `doe analyze --filter-runs IDS` excludes specific run IDs from analysis without editing on-disk files (closes the loop with the high-Cook's-D run IDs Model Adequacy already prints).
- `doe init --template <name>` prints an inferred-goal rationale alongside what the suggester would have recommended for the same factor / response / budget shape.

### Fixed
- Empty-string response values in `run_*.json` no longer raise an opaque `could not convert string to float: ''`; non-numeric values get a file-pointing `ValueError`.
- Replicate detection is now block-aware so block variance can't double-count when blocks are present.
- `_apply_blocks` was stripping `whole_plot_id` from `ExperimentRun`; preserved.
- Cook's distance threshold switched from the aggressive `4/n` rule of thumb to `F(0.5, p, n-p)` (eliminated false-positive flags on small noiseless designs).
- `runner_py.j2` was emitting `SESSION_PREFIX = null` (JSON literal) for the no-session case — fixed to emit literal `None`.
- `--strategy` choices on `doe next-batch` were stuck at `refine|explore|balanced` and silently rejected the newer strategies; CLI now accepts all six.
- `_save_state(state, results_dir)` had one stale call site keeping the legacy signature; phase counters survived `--session` rotation as a result.

## 0.1.0 — 2026-03-27

Initial public release.

- 11 design types: full-factorial, fractional-factorial, Plackett-Burman, Latin hypercube, central composite, Box-Behnken, definitive screening, Taguchi, D-optimal, mixture simplex-lattice, mixture simplex-centroid
- ANOVA analysis with F-tests and p-values
- Main effects and two-factor interaction estimation
- Response surface modeling and optimization
- Multi-objective optimization with desirability functions
- Runner script generation (Bash and Python)
- Interactive HTML report generation
- Design evaluation metrics (D/A/G-efficiency)
- Power analysis
- Design augmentation (fold-over, star points, center points)
