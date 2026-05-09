# doe — User Guide

A practical tour of the DOE helper tool, from first config to a finished
analysis report. Every step links to the relevant CLI subcommand and to
its in-tree reference page.

## Table of Contents
- [Install](#install)
- [The five-step workflow](#the-five-step-workflow)
- [Choose a design](#choose-a-design)
- [Author the test script](#author-the-test-script)
- [Run the experiment](#run-the-experiment)
- [Analyse the results](#analyse-the-results)
- [Iterate](#iterate)
- [Reference](#reference)

---

## Install

```bash
pip install -e ".[dev]"
```

The CLI installs as `doe`. Run `doe --help` to list every subcommand.

---

## The five-step workflow

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────────┐
│ 1. scaffold-    │ →  │ 2. scaffold- │ →  │ 3. generate  │ →  │ 4. run     │ →  │ 5. analyze   │
│    config       │    │    test      │    │              │    │            │    │              │
└─────────────────┘    └──────────────┘    └──────────────┘    └────────────┘    └──────────────┘
       config.json         test.py            run.sh            run_*.json         report.html
```

Every step persists its output on disk so you can re-enter the workflow
at any point.

---

## Choose a design

If you don't already know the right design, ask:

```bash
doe suggest --factors 4 --budget 30 --goal response_surface
```

This prints a recommendation (operation, run count, replicates, blocks,
adaptive strategy) plus a config snippet you can paste straight into
`config.json`.

The decision tree behind it is the standard Box-Hunter-Hunter advice:

| Goal              | Tight budget        | Comfortable budget        |
|-------------------|---------------------|---------------------------|
| screening         | Plackett-Burman     | Fractional factorial Res IV |
| response surface  | definitive_screening | Box-Behnken or central composite |
| optimization      | Latin hypercube + bayesian | LHS seed + bayesian / multi_objective batches |

If you'd rather edit a starter config by hand:

```bash
doe scaffold-config             # writes config.json with sample factors
```

The starter file flags every decision-point with `_<key>_options` showing
the alternatives separated by `|`. Replace the sample factors and pick
one alternative per option-style field.

---

## Author the test script

The runner calls a user-supplied `test_script` once per design row. Don't
hand-author the contract — run

```bash
doe scaffold-test --config config.json [--language py|sh]
```

It writes a starter `test.py` (or `test.sh`) prefilled with the right
argument-parsing block for your `arg_style` (`double-dash` / `env` /
`positional`) and a TODO marking where to plug in your real test. Python
scaffolds use the `doe.runner` helper:

```python
from doe.runner import parse_factors, emit
factors, out = parse_factors(["temperature", "pressure"])
results = run_my_simulation(int(factors["temperature"]),
                            float(factors["pressure"]))
emit(out, throughput=results.throughput, latency=results.latency,
     _expected=["throughput", "latency"])
```

`emit(_expected=...)` validates that you returned every response your
config declares — typos at this layer become a clear error rather than
silently-missing analysis output.

If your "test" is just a Python function (no shell), skip the runner
entirely:

```bash
doe simulate --config config.json --func sim.py:run_one
```

---

## Run the experiment

```bash
doe generate --config config.json [--seed N]
bash run_experiments.sh
```

`doe generate` writes `run_experiments.sh` plus `results/design_matrix.json`
(persisted so analyze and friends are deterministic).

Useful flags:

| Flag                  | What it does                                   |
|-----------------------|------------------------------------------------|
| `--session [PREFIX]`  | Each invocation writes results to a fresh `<out>/<PREFIX>-<TIMESTAMP>/` and updates `<out>/latest`. |
| `--parallel N`        | Emit a `ThreadPoolExecutor` runner with N concurrent workers. |
| `--executor slurm`    | Emit an `sbatch --array` submission. Plus `--slurm-{partition,time,cpus-per-task,mem,max-concurrent}`. |
| `--resolution N`      | For `fractional_factorial`: bump run count until at least Resolution N is achievable. |
| `--replicate-center N` | Append N centre-point runs per block for pure-error / lack-of-fit. |

If you'd rather record results by hand:

```bash
doe record --config config.json --run 1
```

---

## Analyse the results

```bash
doe analyze --config config.json
```

Produces a console report and `results/report.html`. The HTML page has a
sticky table-of-contents at the top.

For each response, `analyze` reports:

- **Main effects** with confidence intervals + Pareto chart.
- **Interaction effects** for two-level factor pairs.
- **ANOVA** with one of five error paths automatically chosen:
  pooled / replicates / Lenth's PSE (unreplicated) / split-plot
  (when `operation: split_plot`) / blocked. Replicate detection is
  block-aware so block variance can't double-count.
- **Ordinal trends** decomposing >2-level factor effects into
  linear + quadratic components.
- **Knee-point detection** (with `--knee`) for saturating curves.
- **Model adequacy**: PRESS / predicted R², Shapiro-Wilk on residuals,
  Durbin-Watson, run-order drift slope, max leverage, max Cook's
  distance with the F(0.5, p, n-p) cutoff.
- **Stationary point** when a quadratic RSM fits — classified as
  maximum / minimum / saddle / ridge / rising_ridge from the Hessian
  eigenvalues, decoded into natural factor units.
- **Achieved power** — per-factor power at δ = 2σ (from the actual
  residual MS) and minimum detectable effect at 80% power.
- **Cross-validation** — k-fold predicted-vs-actual + RMSE / MAE / R²<sub>cv</sub>.
- **Alias structure** when the design is fractional factorial or
  Plackett-Burman.

Skip the per-response RSM refit on big designs: `--no-rsm`.

For variance-based sensitivity over the surrogate:

```bash
doe sensitivity --config config.json --n-samples 1024 --csv sobol.csv
```

---

## Iterate

### Sequential / adaptive batching

```bash
doe next-batch --config config.json
```

Reads the existing results, fits the response surface (or a GP), and
proposes the next batch. Strategy via `cfg.adaptive.strategy`:

| Strategy           | When to use                                              |
|--------------------|----------------------------------------------------------|
| `refine`           | Default. Sample near the current best run.               |
| `explore`          | Space-filling — pick points distant from existing ones.  |
| `balanced`         | Half refine, half explore.                               |
| `model_guided`     | Heuristic surrogate + max-leverage candidates.           |
| `bayesian`         | GP + Expected Improvement (q-EI w/ constant-liar). Single response. |
| `multi_objective`  | One GP per response + random-Tchebycheff EI. ≥2 responses. |

The GP backend (`bayesian` / `multi_objective`) handles numeric **and
categorical** factors via a one-hot + RBF mixed encoder and uses
heteroscedastic noise from replicate scatter when present.

### Comparing sessions

After re-running an experiment with `--session`:

```bash
doe compare --config config.json --baseline results/v1 --candidate results/latest
doe trend   --config config.json --sessions results/v1 results/v2 results/v3
```

`compare` reports paired-run deltas with a t-test and Cohen's d, plus a
session-as-factor regression that splits the change into a uniform
intercept shift versus per-factor slope shifts. `trend` regresses across
≥ 2 sessions and reports per-session means + intercept / slope drift
per session step. Both can write HTML (`--html`) and CSV (`--csv`).

### Calibrating a parametric simulator

```bash
doe calibrate --config config.json \
    --func sim.py:simulate \
    --params noise_level:0.0:1.0 leak_rate:0.0:0.5 \
    --observed results/baseline-20260101 \
    --report calibration.json
```

Fits the simulator's free parameters (with bounds) to observed data via
`scipy.optimize.minimize` and reports RMSE before/after.

### Sharing & reproducing

```bash
doe archive --session results/baseline-20260101 \
            --config config.json --output baseline.tar.gz \
            --extra results/report.html
doe serve --root results/             # browse sessions on localhost
```

Archives include a `manifest.json` with SHA-256 sums for every entry.

---

## Reference

- [`cookbook.md`](cookbook.md) — short recipes for the most common questions ("I have replicates and want lack-of-fit", etc.).
- [`commands.md`](commands.md) — CLI command reference.
- [`strategies.md`](strategies.md) — when to pick which adaptive strategy.
- [`config.md`](config.md) — every config key with defaults.
- [`doe_fundamentals.md`](doe_fundamentals.md) — DOE theory primer.

---

## When things go wrong

| Symptom                                       | Cause / fix                                         |
|-----------------------------------------------|-----------------------------------------------------|
| `could not convert string to float: ''`       | Empty value in a `run_*.json`. Use `--partial` or fix the file. |
| Significant main effect that flips on retest  | Resolution III aliasing — check the alias structure section. |
| `MS_error` is tiny / ~0                       | Fewer params + perfect-fit residuals; pure error needs replicates. |
| Predicted optimum is outside the design region | The response is increasing toward the boundary. Run an `--executor` follow-up to extend. |
| Cook's distance flags too many runs           | Pre-PR #14 the threshold was `4/n`; upgrade to current main where it's `F(0.5, p, n-p)`. |
| `latest` symlink points at a stale session    | Re-run with `--session` to repoint, or pass `--results-dir` explicitly. |
