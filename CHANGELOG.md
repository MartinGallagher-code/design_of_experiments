# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CONTRIBUTING.md with development and PR guidelines
- SECURITY.md for responsible vulnerability disclosure
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- GitHub issue templates (bug report, feature request)
- GitHub pull request template
- Pre-commit configuration for code quality checks

## [0.3.0] — 2026-05-09

### Added
- `doe scaffold-config`, `doe scaffold-test` — annotated starter files
- `doe init --factors --budget --goal [--with-test]` — bootstrap a working config
- `doe suggest` — print a recommended operation + run count + adaptive strategy
- `split_plot` operation with role-based whole-plot / subplot factors
- `--resolution N` knob on `fractional_factorial` with automatic bumping
- `--replicate-center N` for appending centre-point runs per block
- `Factor.dtype: "int"` support (rounded + clamped by all optimisers)
- `Factor.role: "whole_plot"` for split-plot designs
- Constraint expressions via AST allow-list parsing
- Runner formats: `--format sh|py`, `--parallel N`, `--executor slurm`
- `--session [PREFIX]` for timestamped result directories
- D-optimal candidate set enhancements and augmentation
- `doe simulate --func module:fn` for direct Python function driving
- ANOVA path auto-selection (pooled / replicates / Lenth's PSE / split-plot / blocked)
- Model adequacy checks: PRESS, predicted R², Shapiro-Wilk, Durbin-Watson, leverage, Cook's distance
- Stationary point classification from Hessian eigenvalues
- Achieved power retrospective from actual residual MS
- Cross-validation with k-fold predicted-vs-actual (RMSE, MAE, R²_cv)
- Alias structure detection for fractional factorial designs
- Scheffé canonical form for mixture designs
- `doe sensitivity` with Sobol indices and HTML visualizations
- `--no-rsm` flag to skip RSM refit for large designs
- HTML report with sticky table-of-contents
- Six adaptive strategies: `refine`, `explore`, `balanced`, `model_guided`, `bayesian`, `multi_objective`
- `doe calibrate` for parametric simulator fitting
- Adaptive state branching with `--state-name`
- `doe compare` with paired-run delta and Cohen's d
- `doe trend` with multi-session regression
- `doe archive` for tarball bundling with SHA-256 manifest
- `doe serve --root results/` for localhost browsing
- Comprehensive documentation: user_guide, commands, strategies, config, cookbook
- `doe analyze --filter-runs` to exclude outliers without file editing
- `doe init --template <name>` with inferred-goal rationale

### Changed
- README restructured around bootstrap workflow
- Design matrix generation defaults for 2-level factors

### Fixed
- Empty-string response values in `run_*.json` now provide actionable error messages
- Replicate detection made block-aware to prevent variance double-counting
- `_apply_blocks` now preserves `whole_plot_id` in ExperimentRun
- Cook's distance threshold changed from `4/n` to `F(0.5, p, n-p)` rule
- `runner_py.j2` no longer emits `SESSION_PREFIX = null` (now proper `None`)
- `doe next-batch --strategy` now accepts all six strategy options
- `_save_state()` call sites updated to preserve phase counters across sessions

## [0.1.0] — 2026-03-27

### Added
- Initial public release
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

[Unreleased]: https://github.com/MartinGallagher-code/design_of_experiments/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/MartinGallagher-code/design_of_experiments/compare/v0.1.0...v0.3.0
[0.1.0]: https://github.com/MartinGallagher-code/design_of_experiments/releases/tag/v0.1.0
