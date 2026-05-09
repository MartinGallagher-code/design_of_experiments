# Cookbook

Recipes that pair a practical question with the two or three commands
that answer it. For broader context start with the
[user guide](user_guide.md). For everything a flag can do check the
[command reference](commands.md).

Index:
- [Bootstrap a fresh experiment from scratch](#bootstrap-a-fresh-experiment-from-scratch)
- [Screen a long list of factors then refine](#screen-a-long-list-of-factors-then-refine)
- [Add replicates so I can estimate pure error](#add-replicates-so-i-can-estimate-pure-error)
- [Re-analyse without an outlier run](#re-analyse-without-an-outlier-run)
- [Compare yesterday's session against today's](#compare-yesterdays-session-against-todays)
- [Track drift across many sessions](#track-drift-across-many-sessions)
- [Bayesian optimisation loop](#bayesian-optimisation-loop)
- [Calibrate a digital twin against real data](#calibrate-a-digital-twin-against-real-data)
- [Run on Slurm](#run-on-slurm)
- [Restrict the design to a feasible region](#restrict-the-design-to-a-feasible-region)
- [Pin integer factors](#pin-integer-factors)
- [Branch an adaptive trajectory](#branch-an-adaptive-trajectory)
- [Generate a sensitivity report](#generate-a-sensitivity-report)
- [Bundle a session for sharing](#bundle-a-session-for-sharing)
- [Browse all your sessions](#browse-all-your-sessions)
- [Drop the RSM section to make `analyze` fast](#drop-the-rsm-section-to-make-analyze-fast)

---

## Bootstrap a fresh experiment from scratch

```bash
doe init --factors 3 --budget 25 --goal response_surface --with-test
# Edit config.json (rename factors / responses / units)
# Edit test.py (the TODO block)
doe generate --config config.json
bash run_experiments.sh
doe analyze --config config.json
```

The suggester picks an operation that fits your budget and goal (here:
Box-Behnken with three centre points). `--with-test` scaffolds a
matching `test.py` so you only fill in the simulation logic.

---

## Screen a long list of factors then refine

Two phases:

```bash
# Phase 1 — screening
doe init --factors 9 --budget 12 --goal screening
doe generate --config config.json --session screen
bash run_experiments.sh
doe analyze --config config.json
# Inspect the alias structure section + the Pareto chart.
# Note the 3-4 factors that look active.

# Phase 2 — focused RSM on the active factors
# Edit config.json: drop the inactive factors, switch to box_behnken,
# bump budget mentally. Or:
doe scaffold-config --output rsm_config.json
# (and copy the active factors over manually)
doe generate --config rsm_config.json --session rsm
bash run_experiments.sh
doe analyze --config rsm_config.json
```

---

## Add replicates so I can estimate pure error

```json
"settings": {
  "operation": "central_composite",
  "replicate_center": 4
}
```

`doe analyze` will detect the replicates and split error into pure
error + lack-of-fit. The console emits an interpretive note when the
lack-of-fit p-value is below 0.05.

For arbitrary replicates (not centre points), repeat the same factor
settings in your config — the ANOVA path picks them up the same way.

---

## Re-analyse without an outlier run

`doe analyze` flags high-Cook's-distance runs in the Model Adequacy
section. To re-fit excluding them:

```bash
doe analyze --config config.json --filter-runs 7 13
```

Run IDs 7 and 13 are removed from the analysis (they remain on disk
unchanged). The report header notes which IDs were filtered.

---

## Compare yesterday's session against today's

```bash
# Day 1
doe generate --config config.json --session baseline
bash run_experiments.sh

# Day 2 (same config, different lab conditions)
doe generate --config config.json --session followup
bash run_experiments.sh

# Compare
doe compare --config config.json \
    --baseline results/baseline-20260101-093015 \
    --candidate results/followup-20260102-101120 \
    --html compare.html
```

The HTML report shows: paired-run delta dotplot, Cohen's d, per-factor
effect deltas with sign-flip flags, and an intercept-shift vs slope-shift
decomposition.

---

## Track drift across many sessions

```bash
doe trend --config config.json \
    --sessions results/wk1 results/wk2 results/wk3 results/wk4 \
    --html trend.html
```

Reports per-session means + intercept drift per session step (uniform
shift) and per-factor slope drift (whether the response surface itself
is shifting). HTML embeds a per-session-mean line plot with the drift
line overlaid.

---

## Bayesian optimisation loop

```json
"adaptive": {
  "strategy": "bayesian",
  "batch_size": 4,
  "stopping_max_phases": 8
}
```

```bash
# Seed
doe generate --config config.json --session seed
bash run_experiments.sh

# Iterate (run as many phases as you like)
doe next-batch --config config.json --output next.sh
bash next.sh
doe next-batch --config config.json --output next.sh
bash next.sh
# ...
```

For multi-objective use `"strategy": "multi_objective"`. See
[strategies.md](strategies.md) for the picker matrix.

---

## Calibrate a digital twin against real data

You have a parametric simulator and observed data from running the
real experiment:

```bash
doe calibrate --config config.json \
    --func sim.py:simulate \
    --params noise_level:0.0:1.0 leak_rate:0.0:0.3 alpha:0.5:5.0 \
    --observed results/baseline-20260101 \
    --report calibration.json
```

Each `name:low:high` (or `name:initial:low:high`) is a calibration
parameter with bounds. The simulator must accept them as keyword
arguments. RMSE before / after appears in the console; `calibration.json`
captures fitted values + per-response RMSE for the record.

---

## Run on Slurm

```bash
doe generate --config config.json \
    --executor slurm \
    --slurm-partition gpu \
    --slurm-time 02:00:00 \
    --slurm-cpus-per-task 4 \
    --slurm-mem 16G \
    --slurm-max-concurrent 8

sbatch run_experiments.sh   # arrays as 1-N%8
```

The runner is an `sbatch --array` script. To share a session across
multiple submissions, pre-stamp it:

```bash
TS=$(date +%Y%m%d-%H%M%S)
DOE_SESSION_DIR="results/cluster-$TS" sbatch run_experiments.sh
DOE_SESSION_DIR="results/cluster-$TS" sbatch run_experiments.sh  # same session
```

---

## Restrict the design to a feasible region

Mixture-style sum cap, conditional cap, etc.:

```json
"constraints": [
  "x + y + z <= 1.5",
  "catalyst != 'A' or temperature <= 150"
]
```

`doe generate` prints how many runs were filtered. Constraint
expressions parse with an AST allow-list (arithmetic / comparisons /
boolean logic / membership only — no attribute access or imports).

---

## Pin integer factors

```json
{ "name": "threads", "type": "continuous",
  "levels": ["1", "64"], "dtype": "int" }
```

Recommended setpoints from `optimize_surface`, `steepest_ascent`, the
stationary-point decoder, and the `model_guided` / `bayesian` adaptive
strategies are rounded and clamped to the level range.

---

## Branch an adaptive trajectory

```bash
# Default trajectory
doe next-batch --config config.json
bash run_next_batch.sh

# Alternative trajectory (different strategy / batch size)
doe next-batch --config config.json --strategy explore --state-name explore-arm
bash run_next_batch.sh
```

State files live at `cfg.out_directory/adaptive_state[_<name>].json` so
each branch tracks its own phase history. Default state survives
`--session` changes.

---

## Generate a sensitivity report

```bash
doe sensitivity --config config.json --n-samples 1024 \
    --csv sobol.csv --html sobol.html
```

Sobol first-order + total-order indices are computed on the fitted
quadratic RSM via Saltelli sampling. The HTML report shows a
stacked-bar chart per response — bar height is the total-order index;
the lower segment is the first-order share, the upper is the
interaction share.

---

## Bundle a session for sharing

```bash
doe archive \
    --session results/baseline-20260101 \
    --config config.json \
    --output baseline.tar.gz \
    --extra results/report.html \
    --extra sobol.csv
```

The tarball includes a `manifest.json` with SHA-256 sums for every
entry, suitable for filing with a regulator or sharing with a
collaborator.

---

## Browse all your sessions

```bash
doe serve --root results/      # http://127.0.0.1:8000/
```

Stdlib HTTP server. The index page lists every session subdirectory
with links to its rendered HTML report (`report.html`, `compare.html`,
`trend.html` if any) and a "browse files" link to the raw `run_*.json`.

---

## Drop the RSM section to make `analyze` fast

On big designs the per-response quadratic RSM refit dominates
`analyze` runtime. To skip it (and the Model Adequacy / Stationary
Point / Cross-Validation sections it produces):

```bash
doe analyze --config config.json --no-rsm
```

ANOVA, main effects, and the alias structure (where applicable) still
print. Re-run without `--no-rsm` once you've narrowed the analysis.
