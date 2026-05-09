# Command Reference

A one-liner per subcommand plus its most useful flags. Run `doe <cmd> --help`
for the canonical, always-up-to-date list.

## Bootstrapping

| Command                  | What it does |
|--------------------------|--------------|
| `doe scaffold-config`    | Write a starter `config.json` with sample factors + option hints. |
| `doe scaffold-test`      | Write a starter `test.py` / `test.sh` matching the configured `arg_style`. |
| `doe suggest`            | Print a recommended operation + run count + adaptive strategy from `--factors / --responses / --budget / --goal`. |
| `doe init --template <name>` | Extract a built-in use-case template (reactor optimization, etc.) into the current directory. |

## Design generation

| Command           | What it does |
|-------------------|--------------|
| `doe generate`    | Render a runner script + persist `design_matrix.json`. |
| `doe info`        | Print the design summary without writing files. |
| `doe augment`     | Append fold-over / star / centre points to an existing design. |
| `doe export-worksheet` | CSV / Markdown worksheet with one row per run for paper records. |
| `doe export-data` | CSV / TSV of design + responses for spreadsheet analysis. |

`doe generate` flags worth knowing:

| Flag | Effect |
|------|--------|
| `--seed N` | Deterministic randomisation. |
| `--session [PREFIX]` | Each invocation writes results into a fresh `<out>/<PREFIX>-<TIMESTAMP>/` and updates `<out>/latest`. |
| `--parallel N` | `ThreadPoolExecutor` runner with N concurrent workers. |
| `--executor slurm` | Emit `sbatch --array` script. Plus `--slurm-partition`, `--slurm-time`, `--slurm-cpus-per-task`, `--slurm-mem`, `--slurm-max-concurrent`. |
| `--resolution N` | Fractional factorial: bump run count until at least Resolution N. |
| `--replicate-center N` | Append N centre-point runs per block. |
| `--format py` | Emit a Python runner instead of bash. |

## Running

| Command       | What it does |
|---------------|--------------|
| `bash run_experiments.sh` (or `python run_experiments.py`) | Execute every run, write `run_*.json` files. |
| `doe simulate --func module:fn` | Run a Python simulator over the design without going through the runner. |
| `doe record --run N` | Enter results for run N interactively. |
| `doe status`  | Show which runs are complete, which are pending. |

## Analysis

| Command        | What it does |
|----------------|--------------|
| `doe analyze`  | Console summary + `report.html` (effects, ANOVA, interactions, model adequacy, stationary point, achieved power, cross-validation, alias structure). |
| `doe report`   | Re-render the HTML report without the console summary. |
| `doe optimize` | Recommend the optimum factor settings (single or multi-response). |
| `doe power`    | Prospective power analysis from `--sigma` and `--delta` (or post-hoc from results). |
| `doe sensitivity` | Sobol first-order + total-order indices on the fitted RSM. |
| `doe knee` | (Via `doe analyze --knee`.) Detect saturation / breakpoints in response curves. |

`doe analyze` flags:

| Flag | Effect |
|------|--------|
| `--results-dir DIR` | Override the default `out_directory`. Defaults to `<out>/latest` when present. |
| `--partial` | Skip missing run files instead of erroring. |
| `--knee` | Run knee-point detection. |
| `--no-rsm` | Skip the quadratic RSM refit and the model-adequacy / stationary-point / cross-validation sections. |
| `--cv-folds K` | Override the cross-validation fold count (default `min(n, 5)`; pass `n` for LOO). |
| `--no-plots` | Skip writing PNG diagnostic plots. |
| `--no-report` | Skip writing the HTML report. |
| `--csv DIR` | Also export every analysis table as CSV. |

## Iteration & comparison

| Command          | What it does |
|------------------|--------------|
| `doe next-batch` | Fit the surface / GP and propose the next batch. |
| `doe compare --baseline DIR --candidate DIR` | Pairwise comparison: per-run delta + paired t / d, per-factor effect delta with sign-flip flag, intercept-shift vs slope-shift decomposition. |
| `doe trend --sessions DIR1 DIR2 …` | Multi-session regression: per-session means + intercept / slope drift per session step. |
| `doe calibrate --func sim:f --params name:lo:hi --observed DIR` | Fit free parameters in a parametric simulator to observed data. |

## Sharing / browsing

| Command      | What it does |
|--------------|--------------|
| `doe archive --session DIR --output FILE.tar.gz` | Bundle session + config + extras with a SHA-256 manifest. |
| `doe serve --root results/` | Localhost stdlib HTTP server listing sessions and linking to their HTML reports. |
