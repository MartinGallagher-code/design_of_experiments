#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Design of Experiments helper tool — CLI entry point."""

import argparse
from importlib.abc import Traversable
from typing import TypedDict, cast
import csv
import io
import json
import os

from doe.config import load_config
from doe.design import generate_design
from doe.models import (
    AchievedPower,
    AliasEntry,
    AliasStructure,
    AnalysisReport,
    ComparisonReport,
    DesignMatrix,
    DOEConfig,
    ExperimentRun,
    TrendReport,
)


_MATRIX_FILENAME = "design_matrix.json"


class _TemplateInfo(TypedDict):
    """Discovered metadata for a built-in use case template."""
    dir_name: str
    name: str
    description: str
    operation: str
    n_factors: int
    n_responses: int
    path: Traversable


def _save_matrix(matrix: DesignMatrix, directory: str) -> str:
    """Persist the design matrix so that analyze/report/etc. are deterministic."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, _MATRIX_FILENAME)
    data = {
        "factor_names": matrix.factor_names,
        "operation": matrix.operation,
        "metadata": matrix.metadata,
        "runs": [
            {"run_id": r.run_id, "block_id": r.block_id,
             "factor_values": r.factor_values,
             "whole_plot_id": r.whole_plot_id}
            for r in matrix.runs
        ],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def _load_matrix(directory: str) -> DesignMatrix | None:
    """Load a previously saved design matrix, or return None if not found."""
    path = os.path.join(directory, _MATRIX_FILENAME)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    runs = [
        ExperimentRun(
            run_id=r["run_id"],
            block_id=r["block_id"],
            factor_values=r["factor_values"],
            whole_plot_id=r.get("whole_plot_id", 0),
        )
        for r in data["runs"]
    ]
    return DesignMatrix(
        runs=runs,
        factor_names=data["factor_names"],
        operation=data["operation"],
        metadata=data.get("metadata", {}),
    )


def _merge_matrix(base: DesignMatrix, new: DesignMatrix) -> DesignMatrix:
    """Merge new adaptive runs into the base design matrix."""
    existing_ids = {r.run_id for r in base.runs}
    merged_runs = list(base.runs)
    for r in new.runs:
        if r.run_id not in existing_ids:
            merged_runs.append(r)
    return DesignMatrix(
        runs=merged_runs,
        factor_names=base.factor_names,
        operation=base.operation,
        metadata={**base.metadata, "n_total_runs": len(merged_runs)},
    )


def _results_dir_for(cfg: DOEConfig) -> str:
    """Return the results directory for a config."""
    return cfg.out_directory or "results"


def _resolve_results_dir(cfg: DOEConfig, results_dir_arg: str | None) -> str:
    """Pick the results directory for read commands.

    If the user passed --results-dir, use it verbatim. Otherwise prefer
    ``<out>/latest`` when that symlink exists (so session-aware runs are
    picked up automatically), and fall back to ``<out>``.
    """
    if results_dir_arg:
        return results_dir_arg
    base = _results_dir_for(cfg)
    latest = os.path.join(base, "latest")
    if os.path.islink(latest) and os.path.isdir(latest):
        try:
            target = os.readlink(latest)
        except OSError:
            target = ""
        print(f"Using latest session: {latest}" + (f" -> {target}" if target else ""))
        return latest
    return base


def _load_or_generate(cfg: DOEConfig, results_dir: str | None = None) -> DesignMatrix:
    """Load persisted design matrix, falling back to regeneration with a warning."""
    directory = results_dir or _results_dir_for(cfg)
    matrix = _load_matrix(directory)
    if matrix is not None:
        return matrix
    print(
        f"Warning: {_MATRIX_FILENAME} not found in '{directory}'. "
        "Regenerating design without a seed — run-ID mapping may be wrong. "
        "Re-run 'doe generate' to save the matrix."
    )
    return generate_design(cfg)


def _print_version() -> None:
    from doe import __version__
    print(f"doe {__version__}")
    print("Copyright (C) 2026 Martin J. Gallagher")
    print("License: GPL-3.0-or-later <https://www.gnu.org/licenses/gpl-3.0.html>")
    raise SystemExit(0)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doe",
        description="Design of Experiments (DOE) helper tool",
    )
    parser.add_argument(
        "--version", action="store_true", help="show version and exit",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- generate ---
    gen = subparsers.add_parser("generate", help="Generate experiment design and runner script")
    gen.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    gen.add_argument("--output", default="run_experiments.sh", help="Output script path (default: run_experiments.sh)")
    gen.add_argument("--format", choices=["sh", "py"], default="sh", help="Script format: sh (default) or py")
    gen.add_argument("--seed", type=int, default=None, help="Random seed for run order")
    gen.add_argument("--dry-run", action="store_true", help="Print design matrix without writing files")
    gen.add_argument("--session", nargs="?", const="", default=None, metavar="PREFIX",
                     help="Each invocation of the runner creates a fresh "
                          "<out>/<PREFIX>-<TIMESTAMP>/ subdirectory and "
                          "updates <out>/latest to point at it. "
                          "Pass without an argument for timestamp-only.")
    gen.add_argument("--resolution", type=int, default=None, metavar="N",
                     help="For fractional_factorial designs: minimum required "
                          "resolution (3 / 4 / 5+). Bumps run count when "
                          "necessary. Overrides settings.min_resolution.")
    gen.add_argument("--replicate-center", type=int, default=None, metavar="N",
                     dest="replicate_center",
                     help="Append N center-point runs to each block for a "
                          "pure-error / lack-of-fit estimate. Requires at "
                          "least one factor with two numeric levels. "
                          "Overrides settings.replicate_center.")
    gen.add_argument("--parallel", type=int, default=1, metavar="N",
                     help="Emit a thread-pool Python runner that submits N "
                          "test_script invocations concurrently. N=1 (default) "
                          "uses the standard sequential runner. Use this when "
                          "each test invocation is independent and bounded I/O.")
    gen.add_argument("--executor", choices=["local", "slurm"], default="local",
                     help="Runner backend (default: local). 'slurm' emits an "
                          "sbatch --array submission script.")
    gen.add_argument("--slurm-partition", default=None, metavar="NAME",
                     help="Slurm partition (only with --executor slurm)")
    gen.add_argument("--slurm-time", default=None, metavar="HH:MM:SS",
                     help="Wall-time per array task (only with --executor slurm)")
    gen.add_argument("--slurm-cpus-per-task", type=int, default=None, metavar="N",
                     help="CPUs per array task (only with --executor slurm)")
    gen.add_argument("--slurm-mem", default=None, metavar="SIZE",
                     help="Memory per task, e.g. '4G' (only with --executor slurm)")
    gen.add_argument("--slurm-max-concurrent", type=int, default=None, metavar="N",
                     help="Cap concurrently running array tasks via 'array=1-N%%K' "
                          "(only with --executor slurm)")

    # --- analyze ---
    ana = subparsers.add_parser("analyze", help="Analyze completed experiment results")
    ana.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ana.add_argument("--results-dir", default=None, help="Override out_directory from config")
    ana.add_argument("--no-plots", action="store_true", help="Skip generating plots")
    ana.add_argument("--no-report", action="store_true", help="Skip generating the HTML report")
    ana.add_argument("--csv", default=None, metavar="DIR", help="Export analysis results to CSV files in DIR")
    ana.add_argument("--partial", action="store_true", help="Analyze only completed runs, skipping missing results")
    ana.add_argument("--knee", action="store_true", help="Detect saturation/knee points in response curves")
    ana.add_argument("--factor", nargs="+", metavar="NAME", help="Analyze only the specified factor(s)")
    ana.add_argument("--filter-runs", nargs="+", type=int, default=None, metavar="ID",
                     help="Exclude these run IDs from the analysis (e.g. flagged outliers). "
                          "The on-disk result files are left unchanged.")
    ana.add_argument("--no-rsm", action="store_true",
                     help="Skip the quadratic RSM refit (and therefore the "
                          "Model Adequacy and Stationary Point sections). "
                          "Useful on large designs where analyze is slow.")
    ana.add_argument("--cv-folds", type=int, default=None, metavar="K",
                     help="Number of cross-validation folds for the response "
                          "surface (default: min(n, 5); set to n for "
                          "leave-one-out).")

    # --- info ---
    info = subparsers.add_parser("info", help="Show design info without generating anything")
    info.add_argument("--config", required=True, metavar="FILE")

    # --- optimize ---
    opt = subparsers.add_parser("optimize", help="Recommend optimal factor settings from results")
    opt.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    opt.add_argument("--results-dir", default=None, help="Override out_directory from config")
    opt.add_argument("--response", default=None, help="Optimize for a specific response (default: all)")
    opt.add_argument("--partial", action="store_true", help="Analyze only completed runs, skipping missing results")
    opt.add_argument("--multi", action="store_true", help="Multi-objective optimization using desirability functions")
    opt.add_argument("--steepest", action="store_true", help="Show steepest ascent/descent pathway")

    # --- report ---
    rep = subparsers.add_parser("report", help="Generate an interactive HTML report")
    rep.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    rep.add_argument("--results-dir", default=None, help="Override out_directory from config")
    rep.add_argument("--output", default="report.html", help="Output HTML file path")
    rep.add_argument("--partial", action="store_true", help="Analyze only completed runs, skipping missing results")
    rep.add_argument("--include", action="append", default=[], metavar="FILE",
                     help="Inline another HTML file (e.g. compare.html, trend.html, "
                          "sobol.html) as an extra section in this report. Repeat the "
                          "flag for multiple files.")

    # --- record ---
    rec = subparsers.add_parser("record", help="Interactively record results for experiment runs")
    rec.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    rec.add_argument("--run", required=True, help="Run number to record (or 'all' for pending runs)")
    rec.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")

    # --- status ---
    sta = subparsers.add_parser("status", help="Show experiment progress")
    sta.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    sta.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")

    # --- power ---
    pwr = subparsers.add_parser("power", help="Compute statistical power for each factor")
    pwr.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    pwr.add_argument("--sigma", type=float, default=None, help="Error standard deviation (estimated from results if omitted)")
    pwr.add_argument("--delta", type=float, default=None, help="Minimum detectable effect size")
    pwr.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    pwr.add_argument("--results-dir", default=None, help="Override out_directory from config")
    pwr.add_argument("--partial", action="store_true", help="Analyze only completed runs")

    # --- augment ---
    aug = subparsers.add_parser("augment", help="Augment an existing design with additional runs")
    aug.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    aug.add_argument("--type", required=True, choices=["fold_over", "star_points", "center_points", "d_optimal"],
                     help="Type of augmentation")
    aug.add_argument("--output", default="run_experiments_augmented.sh", help="Output script path")
    aug.add_argument("--format", choices=["sh", "py"], default="sh", help="Script format")
    aug.add_argument("--seed", type=int, default=None, help="Random seed for run order")
    aug.add_argument("--session", nargs="?", const="", default=None, metavar="PREFIX",
                     help="Generate a session-aware runner (see 'doe generate --session').")

    # --- init ---
    init = subparsers.add_parser("init", help="Create a new experiment from a built-in template OR from --factors/--budget/--goal")
    init.add_argument("--template", default=None, metavar="NAME",
                       help="Use case template name (e.g. reactor_optimization, coffee_brewing)")
    init.add_argument("--list", action="store_true", dest="list_templates",
                       help="List all available use case templates")
    init.add_argument("--output-dir", default=".", metavar="DIR",
                       help="Directory to extract the template into (default: current directory)")
    init.add_argument("--factors", type=int, default=None, metavar="N",
                       help="Bootstrap a fresh config for N factors (skips templates).")
    init.add_argument("--responses", type=int, default=1, metavar="M",
                       help="Response count when bootstrapping (default: 1)")
    init.add_argument("--budget", type=int, default=None, metavar="K",
                       help="Run budget when bootstrapping; required with --factors.")
    init.add_argument("--goal", choices=["screening", "response_surface", "optimization"],
                       default="screening",
                       help="Goal when bootstrapping (default: screening)")
    init.add_argument("--categorical", type=int, default=0, metavar="N",
                       help="Number of categorical factors when bootstrapping")
    init.add_argument("--with-test", action="store_true",
                       help="Also scaffold a test.py beside the new config")

    # --- export-worksheet ---
    ew = subparsers.add_parser("export-worksheet", help="Export design as a printable worksheet")
    ew.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ew.add_argument("--format", choices=["csv", "markdown"], default="csv", help="Output format (default: csv)")
    ew.add_argument("--output", default=None, metavar="FILE", help="Output file path (default: stdout)")
    ew.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")

    # --- export-data ---
    ed = subparsers.add_parser("export-data", help="Export design matrix and response values as CSV/TSV")
    ed.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ed.add_argument("--format", choices=["csv", "tsv"], default="csv", help="Output format (default: csv)")
    ed.add_argument("--output", default=None, metavar="FILE", help="Output file path (default: stdout)")
    ed.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")
    ed.add_argument("--partial", action="store_true", help="Include runs with missing results")

    # --- compare ---
    cmp = subparsers.add_parser(
        "compare",
        help="Pairwise comparison between two result sessions",
    )
    cmp.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    cmp.add_argument("--baseline", required=True, metavar="DIR",
                     help="Baseline session directory (e.g. results/baseline-20260101-093015)")
    cmp.add_argument("--candidate", required=True, metavar="DIR",
                     help="Candidate session directory (e.g. results/latest)")
    cmp.add_argument("--csv", default=None, metavar="DIR",
                     help="Also export the comparison tables to this directory")
    cmp.add_argument("--html", default=None, metavar="FILE",
                     help="Also write a self-contained HTML comparison page")

    # --- trend ---
    trd = subparsers.add_parser(
        "trend",
        help="Multi-session trend analysis (regression across N >= 2 sessions)",
    )
    trd.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    trd.add_argument("--sessions", required=True, nargs="+", metavar="DIR",
                     help="Session directories in chronological order (oldest first).")
    trd.add_argument("--csv", default=None, metavar="DIR",
                     help="Also export the trend tables to this directory")
    trd.add_argument("--html", default=None, metavar="FILE",
                     help="Also write a self-contained HTML trend page")

    # --- archive ---
    arc = subparsers.add_parser(
        "archive",
        help="Bundle a session directory into a reproducible tar.gz with a manifest",
    )
    arc.add_argument("--session", required=True, metavar="DIR",
                     help="Session directory (e.g. results/baseline-20260101)")
    arc.add_argument("--output", required=True, metavar="FILE",
                     help="Output archive path (e.g. baseline.tar.gz)")
    arc.add_argument("--config", default=None, metavar="FILE",
                     help="Optional config file to embed alongside the session")
    arc.add_argument("--extra", action="append", default=[], metavar="FILE",
                     help="Extra file(s) to embed (HTML report, CSV exports, etc.). "
                          "Repeat the flag to add more than one.")

    # --- suggest ---
    sg = subparsers.add_parser(
        "suggest",
        help="Recommend a DOE design given factor count, run budget, and goal",
    )
    sg.add_argument("--factors", type=int, required=True, metavar="N",
                    help="Number of factors")
    sg.add_argument("--responses", type=int, default=1, metavar="M",
                    help="Number of responses (default: 1)")
    sg.add_argument("--budget", type=int, required=True, metavar="K",
                    help="Maximum runs you can afford")
    sg.add_argument("--goal", choices=["screening", "response_surface", "optimization"],
                    default="screening",
                    help="What you're trying to learn (default: screening)")
    sg.add_argument("--categorical", type=int, default=0, metavar="N",
                    help="Number of categorical factors (rest are treated as continuous)")

    # --- sensitivity ---
    sens = subparsers.add_parser(
        "sensitivity",
        help="Compute Sobol indices on the fitted RSM (variance-based sensitivity)",
    )
    sens.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    sens.add_argument("--results-dir", default=None, help="Override out_directory from config")
    sens.add_argument("--response", default=None,
                      help="Compute indices for this response only (default: every response)")
    sens.add_argument("--n-samples", type=int, default=512, metavar="N",
                      help="Saltelli base sample count N. Total evaluations = N*(k+2). "
                           "Default 512.")
    sens.add_argument("--csv", default=None, metavar="FILE",
                      help="Optional CSV output path")
    sens.add_argument("--html", default=None, metavar="FILE",
                      help="Optional self-contained HTML report with stacked-bar plots")
    sens.add_argument("--seed", type=int, default=42)
    sens.add_argument("--partial", action="store_true",
                      help="Analyse only completed runs, skipping missing results")

    # --- calibrate ---
    cal = subparsers.add_parser(
        "calibrate",
        help="Fit free parameters in a parametric simulator to observed data",
    )
    cal.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    cal.add_argument("--func", required=True, metavar="TARGET",
                     help="Parametric simulator as 'module:function' or 'path.py:function'")
    cal.add_argument("--params", required=True, nargs="+", metavar="SPEC",
                     help="Parameter specs as 'name:low:high' or 'name:initial:low:high'.")
    cal.add_argument("--observed", required=True, metavar="DIR",
                     help="Session directory holding the observed (real-world) results")
    cal.add_argument("--report", default=None, metavar="FILE",
                     help="Optional path to write the JSON calibration report")
    cal.add_argument("--seed", type=int, default=42,
                     help="Random seed for design generation (default: 42)")

    # --- simulate ---
    sim = subparsers.add_parser(
        "simulate",
        help="Run a Python function over the design matrix instead of an external script",
    )
    sim.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    sim.add_argument("--func", required=True, metavar="TARGET",
                     help="Python target as 'module:function' or 'path/to/file.py:function'. "
                          "The function takes a dict[str, str] of factor values and returns "
                          "a dict[str, float] of response values.")
    sim.add_argument("--results-dir", default=None, metavar="DIR",
                     help="Override out_directory from config")
    sim.add_argument("--session", nargs="?", const="", default=None, metavar="PREFIX",
                     help="Write results into a session subdirectory (same semantics as "
                          "'doe generate --session').")
    sim.add_argument("--overwrite", action="store_true",
                     help="Re-evaluate runs whose result file already exists")
    sim.add_argument("--seed", type=int, default=42,
                     help="Random seed for design generation (default: 42)")

    # --- serve ---
    srv = subparsers.add_parser(
        "serve",
        help="Browse session results from a localhost web page",
    )
    srv.add_argument("--root", default="results", metavar="DIR",
                     help="Directory containing session subdirectories (default: results)")
    srv.add_argument("--host", default="127.0.0.1",
                     help="Bind address (default: 127.0.0.1)")
    srv.add_argument("--port", type=int, default=8000,
                     help="Bind port (default: 8000)")

    # --- scaffold-config ---
    sfc = subparsers.add_parser(
        "scaffold-config",
        help="Generate a starter config.json with sample factors and option hints",
    )
    sfc.add_argument("--output", default="config.json", metavar="FILE",
                     help="Output path (default: config.json)")
    sfc.add_argument("--force", action="store_true",
                     help="Overwrite the output file if it already exists")

    # --- scaffold-test ---
    scf = subparsers.add_parser(
        "scaffold-test",
        help="Generate a starter test_script prefilled from the config",
    )
    scf.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    scf.add_argument("--language", choices=["py", "sh"], default="py",
                     help="Language for the scaffolded test script (default: py)")
    scf.add_argument("--output", default=None, metavar="FILE",
                     help="Output path (default: test.py / test.sh)")
    scf.add_argument("--force", action="store_true",
                     help="Overwrite the output file if it already exists")

    # --- next-batch ---
    nb = subparsers.add_parser("next-batch", help="Generate next batch of adaptive experiment runs")
    nb.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    nb.add_argument("--results-dir", default=None, help="Override out_directory from config")
    nb.add_argument("--strategy",
                    choices=["refine", "explore", "balanced",
                             "model_guided", "bayesian", "multi_objective"],
                    default=None,
                    help="Override strategy from config")
    nb.add_argument("--batch-size", type=int, default=None, help="Override batch size from config")
    nb.add_argument("--output", default="run_next_batch.sh", help="Output script path")
    nb.add_argument("--format", choices=["sh", "py"], default="sh", help="Script format")
    nb.add_argument("--seed", type=int, default=None, help="Random seed")
    nb.add_argument("--partial", action="store_true", help="Analyze only completed runs")
    nb.add_argument("--session", nargs="?", const="", default=None, metavar="PREFIX",
                    help="Generate a session-aware runner (see 'doe generate --session').")
    nb.add_argument("--state-name", default=None, metavar="NAME",
                    help="Branch the adaptive trajectory by writing state to "
                         "'adaptive_state_<NAME>.json' under cfg.out_directory. "
                         "Default state file persists across --session switches.")

    args = parser.parse_args()

    if args.version:
        _print_version()

    if not args.command:
        parser.print_help()
        raise SystemExit(1)

    try:
        _dispatch(args)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in config file: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except PermissionError as e:
        print(f"Error: {e}")
    except OSError as e:
        if "No such file or directory" in str(e):
            print(f"Error: {e}")
        else:
            raise


def _dispatch(args: argparse.Namespace) -> None:
    """Dispatch to the appropriate subcommand handler."""
    if args.command == "generate":
        cfg = load_config(args.config)
        if args.resolution is not None:
            cfg.min_resolution = int(args.resolution)
        if args.replicate_center is not None:
            cfg.replicate_center = int(args.replicate_center)
        matrix = generate_design(cfg, seed=args.seed)
        if args.dry_run:
            _print_matrix(matrix, cfg)
        else:
            from doe.codegen import generate_script
            slurm_options = {
                "partition": args.slurm_partition,
                "time": args.slurm_time,
                "cpus_per_task": args.slurm_cpus_per_task,
                "mem": args.slurm_mem,
                "max_concurrent": args.slurm_max_concurrent,
            }
            generate_script(
                matrix, cfg, args.output, format=args.format,
                session_prefix=args.session,
                parallel_workers=max(1, args.parallel),
                executor=args.executor,
                slurm_options=slurm_options,
            )
            out_dir = _results_dir_for(cfg)
            _save_matrix(matrix, out_dir)
            print(f"Generated {len(matrix.runs)} runs -> {args.output}")
            print(f"Run with: bash {args.output}")
            if args.session is not None:
                label = args.session or "(timestamp only)"
                print(f"Each invocation will create a new session under "
                      f"{out_dir}/ (prefix: {label}); {out_dir}/latest will "
                      f"track the most recent session.")

    elif args.command == "analyze":
        cfg = load_config(args.config)
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        matrix = _load_or_generate(cfg, results_dir=results_dir)
        try:
            from doe.analysis import analyze
            report = analyze(matrix, cfg, results_dir=results_dir, no_plots=args.no_plots, partial=args.partial, detect_knee=args.knee, filter_factors=args.factor, exclude_run_ids=args.filter_runs, fit_rsm=not args.no_rsm, cv_folds=args.cv_folds)
            if args.filter_runs:
                print(f"\nNote: excluded run IDs from analysis: {sorted(args.filter_runs)}")
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return
        _print_report(report)
        if args.csv:
            from doe.analysis import export_csv
            csv_files = export_csv(report, args.csv)
            for p in csv_files:
                print(f"CSV exported: {p}")
        if not args.no_report:
            from doe.report import generate_report
            processed_dir = cfg.processed_directory or cfg.out_directory or "results"
            report_path = os.path.join(processed_dir, "report.html")
            generate_report(matrix, cfg, results_dir=results_dir, output_path=report_path, partial=args.partial, filter_factors=args.factor)
            print(f"\nHTML report: {report_path}")

    elif args.command == "info":
        cfg = load_config(args.config, strict=False)
        matrix = generate_design(cfg)
        _print_matrix(matrix, cfg)
        # Show design evaluation metrics
        try:
            from doe.design import evaluate_design
            metrics = evaluate_design(matrix, cfg)
            if metrics:
                print("\nDesign Evaluation Metrics:")
                print(f"  D-efficiency: {metrics.get('d_efficiency', 0):.1f}%")
                print(f"  A-efficiency: {metrics.get('a_efficiency', 0):.4f}")
                print(f"  G-efficiency: {metrics.get('g_efficiency', 0):.1f}%")
        except Exception:
            pass

    elif args.command == "optimize":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        try:
            _run_optimize(matrix, cfg, args)
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return

    elif args.command == "report":
        cfg = load_config(args.config)
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        matrix = _load_or_generate(cfg, results_dir=results_dir)
        try:
            from doe.report import generate_report
            generate_report(matrix, cfg, results_dir=results_dir, output_path=args.output, partial=args.partial, include_paths=args.include)
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return

    elif args.command == "record":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        _handle_record(matrix, cfg, args.run)

    elif args.command == "status":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        _handle_status(matrix, cfg)

    elif args.command == "power":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        _handle_power(matrix, cfg, args)

    elif args.command == "augment":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        from doe.design import augment_design
        augmented = augment_design(matrix, cfg, augment_type=args.type)
        from doe.codegen import generate_script
        generate_script(augmented, cfg, args.output, format=args.format,
                        session_prefix=args.session)
        out_dir = _results_dir_for(cfg)
        _save_matrix(augmented, out_dir)
        n_new = augmented.metadata.get("n_augmented_runs", 0)
        print(f"Augmented design: {len(matrix.runs)} original + {n_new} new = {len(augmented.runs)} total runs")
        print(f"Generated -> {args.output}")

    elif args.command == "init":
        _handle_init(args)

    elif args.command == "export-worksheet":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        _handle_export_worksheet(matrix, cfg, fmt=args.format, output_path=args.output)

    elif args.command == "export-data":
        cfg = load_config(args.config)
        matrix = _load_or_generate(cfg)
        _handle_export_data(matrix, cfg, fmt=args.format, output_path=args.output,
                            partial=args.partial)

    elif args.command == "suggest":
        from doe.suggest import suggest
        kinds = ["categorical"] * args.categorical + (
            ["continuous"] * (args.factors - args.categorical)
        )
        recommendation = suggest(
            n_factors=args.factors, n_responses=args.responses,
            budget=args.budget, goal=args.goal, factor_kinds=kinds,
        )
        print("\n=== Suggestion ===")
        print(f"  operation        : {recommendation.operation}")
        print(f"  estimated runs   : {recommendation.estimated_runs}")
        if recommendation.block_count > 1:
            print(f"  block_count      : {recommendation.block_count}")
        if recommendation.replicate_center:
            print(f"  replicate_center : {recommendation.replicate_center}")
        if recommendation.min_resolution:
            print(f"  min_resolution   : {recommendation.min_resolution}")
        if recommendation.adaptive_strategy:
            print(f"  adaptive.strategy: {recommendation.adaptive_strategy}")
        for line in recommendation.rationale:
            print(f"  - {line}")
        for note in recommendation.notes:
            print(f"  Note: {note}")
        print()
        print("  Sketch this into your config:")
        snippet = (
            '    "settings": {\n'
            f'      "operation": "{recommendation.operation}",\n'
        )
        if recommendation.block_count > 1:
            snippet += f'      "block_count": {recommendation.block_count},\n'
        if recommendation.replicate_center:
            snippet += f'      "replicate_center": {recommendation.replicate_center},\n'
        if recommendation.min_resolution:
            snippet += f'      "min_resolution": {recommendation.min_resolution},\n'
        snippet += '      ...\n    }'
        if recommendation.adaptive_strategy:
            snippet += (
                ',\n    "adaptive": { "strategy": "'
                + recommendation.adaptive_strategy + '", "batch_size": 4 }'
            )
        print(snippet)

    elif args.command == "sensitivity":
        cfg = load_config(args.config, strict=False)
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        matrix = _load_or_generate(cfg, results_dir=results_dir)
        _handle_sensitivity(matrix, cfg, results_dir, args)

    elif args.command == "calibrate":
        cfg = load_config(args.config, strict=False)
        matrix = _load_or_generate(cfg)
        from doe.calibrate import (
            calibrate, parse_param_spec, load_observed,
            write_calibration_report,
        )
        param_specs = [parse_param_spec(s) for s in args.params]
        observed = load_observed(args.observed, matrix.runs)
        result = calibrate(matrix.runs, observed, args.func, param_specs)
        print("\n=== Calibration ===")
        print(f"  RMSE before: {result.rmse_before:.4f}")
        print(f"  RMSE after : {result.rmse_after:.4f}"
              f"   ({'converged' if result.converged else 'did not converge'},"
              f" {result.n_iterations} iterations)")
        print("  Fitted parameters:")
        for name, value in result.fitted_params.items():
            low, high = result.bounds[name]
            initial = result.initial_params[name]
            print(f"    {name:<20} = {value:.6g}   (init {initial:.6g}, "
                  f"bounds [{low:.4g}, {high:.4g}])")
        if result.per_response_rmse:
            print("  Per-response RMSE:")
            for resp_name, rmse in result.per_response_rmse.items():
                print(f"    {resp_name:<20} = {rmse:.4f}")
        if args.report:
            write_calibration_report(result, args.report)
            print(f"  Report -> {args.report}")

    elif args.command == "simulate":
        cfg = load_config(args.config, strict=False)
        matrix = _load_or_generate(cfg, results_dir=args.results_dir)
        from doe.simulate import simulate
        simulate(
            matrix, cfg, func=args.func,
            output_dir=args.results_dir,
            session_prefix=args.session,
            overwrite=args.overwrite,
        )

    elif args.command == "serve":
        from doe.serve import serve
        serve(root=args.root, host=args.host, port=args.port)

    elif args.command == "archive":
        from doe.archive import archive_session
        manifest = archive_session(
            session_dir=args.session,
            output_path=args.output,
            config_path=args.config,
            extras=args.extra,
        )
        print(f"Wrote archive -> {args.output}")
        print(f"  files     : {len(manifest['files'])}")
        print(f"  session   : {manifest['session_dir']}")
        if manifest['config_path']:
            print(f"  config    : {manifest['config_path']}")

    elif args.command == "trend":
        cfg = load_config(args.config, strict=False)
        from doe.trend import trend_sessions
        trend_report = trend_sessions(cfg, args.sessions)
        _print_trend_report(trend_report)
        if args.csv:
            from doe.trend import export_trend_csv
            paths = export_trend_csv(trend_report, args.csv)
            for p in paths:
                print(f"CSV exported: {p}")
        if args.html:
            from doe.trend import export_trend_html
            export_trend_html(trend_report, args.html)
            print(f"HTML report: {args.html}")

    elif args.command == "compare":
        cfg = load_config(args.config, strict=False)
        from doe.compare import compare_sessions
        compare_report = compare_sessions(cfg, args.baseline, args.candidate)
        _print_compare_report(compare_report)
        if args.csv:
            from doe.compare import export_compare_csv
            paths = export_compare_csv(compare_report, args.csv)
            for p in paths:
                print(f"CSV exported: {p}")
        if args.html:
            from doe.compare import export_compare_html
            export_compare_html(compare_report, args.html)
            print(f"HTML report: {args.html}")

    elif args.command == "scaffold-config":
        if os.path.exists(args.output) and not args.force:
            print(
                f"Error: '{args.output}' already exists. "
                f"Pass --force to overwrite or --output FILE to write elsewhere."
            )
            return
        from doe.codegen import generate_config_template
        generate_config_template(args.output)
        print(f"Wrote starter config -> {args.output}")
        print()
        print("Next steps:")
        print(f"  1. Edit {args.output} — replace sample factors / responses with your own.")
        print(f"     Values containing ' | ' list alternatives; pick one.")
        print(f"  2. doe scaffold-test --config {args.output}    # generates test.py")
        print(f"  3. doe info --config {args.output}             # preview the design")
        print(f"  4. doe generate --config {args.output}         # emit the runner script")

    elif args.command == "scaffold-test":
        cfg = load_config(args.config, strict=False)
        default_name = "test.py" if args.language == "py" else "test.sh"
        output_path = args.output or default_name
        if os.path.exists(output_path) and not args.force:
            print(
                f"Error: '{output_path}' already exists. "
                f"Pass --force to overwrite or --output FILE to write elsewhere."
            )
            return
        from doe.codegen import generate_test_scaffold
        generate_test_scaffold(cfg, output_path, language=args.language)
        print(f"Wrote test scaffold -> {output_path}")
        print("Edit the TODO block, then point your config at it:")
        print(f'  "settings": {{ "test_script": "{output_path}" }}')

    elif args.command == "next-batch":
        cfg = load_config(args.config)
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        matrix = _load_or_generate(cfg, results_dir=results_dir)
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        adaptive_cfg: AdaptiveConfig = (
            cfg.adaptive if isinstance(cfg.adaptive, AdaptiveConfig)
            else AdaptiveConfig()
        )
        if args.strategy:
            adaptive_cfg.strategy = args.strategy
        if args.batch_size:
            adaptive_cfg.batch_size = args.batch_size
        try:
            new_matrix, state = plan_next_batch(
                matrix, cfg, adaptive_cfg,
                results_dir=results_dir, seed=args.seed,
                state_name=args.state_name,
            )
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return
        if state.should_stop:
            print(f"Stopping recommended: {state.stop_reason}")
            print(f"Completed {state.phase} phases with {state.total_runs} total runs.")
        else:
            from doe.codegen import generate_script
            generate_script(new_matrix, cfg, args.output, format=args.format,
                            session_prefix=args.session)
            # Merge new runs into the saved matrix so analyze sees them
            merged = _merge_matrix(matrix, new_matrix)
            out_dir = args.results_dir or _results_dir_for(cfg)
            _save_matrix(merged, out_dir)
            print(f"Phase {state.phase}: generated {len(new_matrix.runs)} new runs -> {args.output}")
            print(f"Design matrix updated: {len(merged.runs)} total runs")


def _no_results_message(cfg: DOEConfig, matrix: DesignMatrix) -> None:
    """Print a friendly message when results are missing."""
    results_dir = cfg.out_directory or "results"
    n_runs = len(matrix.runs)
    print(f"No results found in '{results_dir}/'.")
    print()
    print(f"This experiment has {n_runs} runs that need to be completed first.")
    print(f"To run the experiment:")
    if not cfg.test_script:
        print(f"  1. doe scaffold-test --config config.json   # creates test.py")
        print(f"  2. edit test.py and add it as test_script in your config")
        print(f"  3. doe generate --config config.json --output {results_dir}/run.sh")
        print(f"  4. bash {results_dir}/run.sh")
    else:
        print(f"  1. doe generate --config config.json --output {results_dir}/run.sh")
        print(f"  2. bash {results_dir}/run.sh")
    print()
    print(f"Or record results manually:")
    print(f"  doe record --config config.json --run 1")
    print()
    print(f"To analyze partial results (completed runs only):")
    print(f"  doe analyze --config config.json --partial")


def _run_optimize(matrix: DesignMatrix, cfg: DOEConfig, args: argparse.Namespace) -> None:
    """Run the optimize subcommand (steepest, multi, or single-response)."""
    if args.steepest:
        from doe.analysis import _load_all_results, _coerce_response_value
        from doe.rsm import fit_rsm, steepest_ascent as _steepest
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        all_data = _load_all_results(matrix.runs, results_dir, partial=args.partial)
        for resp in cfg.responses:
            responses = {}
            for run in matrix.runs:
                data = all_data.get(run.run_id, {})
                value = _coerce_response_value(data, resp.name, run.run_id, results_dir)
                if value is not None:
                    responses[run.run_id] = value
            if not responses:
                continue
            valid_runs = [r for r in matrix.runs if r.run_id in responses]
            model = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="linear")
            pathway = _steepest(model, matrix.factor_names, cfg.factors, direction=resp.optimize)
            print(f"\n=== Steepest {'Ascent' if resp.optimize == 'maximize' else 'Descent'}: {resp.name} ===")
            print(f"{'Step':<6}", end="")
            for fname in matrix.factor_names:
                print(f"{fname:>14}", end="")
            print(f"{'Predicted':>14}")
            print("-" * (6 + 14 * (len(matrix.factor_names) + 1)))
            for pt in pathway:
                print(f"{pt['step']:<6}", end="")
                settings = cast("dict[str, object]", pt['settings'])
                for fname in matrix.factor_names:
                    print(f"{settings[fname]:>14}", end="")
                print(f"{pt['predicted_value']:>14.4f}")
    elif args.multi:
        from doe.optimize import multi_objective
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        multi_objective(matrix, cfg, results_dir=results_dir, partial=args.partial)
    else:
        from doe.optimize import recommend
        results_dir = _resolve_results_dir(cfg, args.results_dir)
        recommend(matrix, cfg, results_dir=results_dir, response_name=args.response, partial=args.partial)


def _handle_init_bootstrap(args: argparse.Namespace) -> None:
    """Bootstrap a working config (and optionally a test.py) from
    --factors / --responses / --budget / --goal, using the same logic
    as 'doe suggest'."""
    if args.budget is None:
        print("Error: --budget is required when bootstrapping with --factors.")
        return
    if args.factors < 1 or args.budget < 1:
        print("Error: --factors and --budget must both be positive.")
        return
    if args.categorical < 0 or args.categorical > args.factors:
        print(
            f"Error: --categorical ({args.categorical}) must be between "
            f"0 and --factors ({args.factors})."
        )
        return

    from doe.suggest import suggest
    from doe.codegen import generate_config_template, generate_test_scaffold
    from doe.config import load_config

    out_dir = args.output_dir or "."
    os.makedirs(out_dir, exist_ok=True)
    config_path = os.path.join(out_dir, "config.json")
    test_path = os.path.join(out_dir, "test.py") if args.with_test else None

    if os.path.exists(config_path):
        print(f"Error: '{config_path}' already exists; refusing to overwrite.")
        return
    if test_path and os.path.exists(test_path):
        print(f"Error: '{test_path}' already exists; refusing to overwrite.")
        return

    kinds = (
        ["categorical"] * args.categorical
        + ["continuous"] * (args.factors - args.categorical)
    )
    rec = suggest(
        n_factors=args.factors, n_responses=args.responses,
        budget=args.budget, goal=args.goal, factor_kinds=kinds,
    )

    # Write a starter config and overlay the suggested operation / settings.
    generate_config_template(config_path)
    with open(config_path) as f:
        cfg_dict = json.load(f)

    # Replace the sample factors with the requested mix.
    cfg_dict["factors"] = _bootstrap_factors(args.factors, args.categorical)
    cfg_dict["fixed_factors"] = {}
    cfg_dict["responses"] = [
        {"name": f"response_{i + 1}",
         "optimize": "maximize" if i % 2 == 0 else "minimize"}
        for i in range(max(1, args.responses))
    ]
    cfg_dict["settings"]["operation"] = rec.operation
    if rec.replicate_center:
        cfg_dict["settings"]["replicate_center"] = rec.replicate_center
    if rec.min_resolution:
        cfg_dict["settings"]["min_resolution"] = rec.min_resolution
    if rec.block_count > 1:
        cfg_dict["settings"]["block_count"] = rec.block_count
    if rec.adaptive_strategy:
        cfg_dict["adaptive"] = {
            "strategy": rec.adaptive_strategy,
            "batch_size": 4,
            "stopping_max_phases": 5,
        }
        cfg_dict.pop("_adaptive", None)
        cfg_dict.pop("_adaptive_help", None)
    cfg_dict["metadata"] = {
        "name": f"{args.goal.replace('_', ' ').title()} (bootstrapped)",
        "description": (
            f"Auto-generated for {args.factors} factor(s), {args.responses} "
            f"response(s), budget {args.budget}, goal '{args.goal}'."
        ),
    }
    cfg_dict["_help"] = (
        "Bootstrapped by 'doe init --factors ... --budget ... --goal ...'. "
        "Replace 'factor_1' / 'response_1' names with your own; tweak "
        "levels and units. The suggester chose '"
        + rec.operation + "' — see docs/strategies.md for alternatives."
    )

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg_dict, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {config_path}")
    print(f"  goal      : {args.goal}")
    print(f"  factors   : {args.factors} ({args.categorical} categorical)")
    print(f"  responses : {args.responses}")
    print(f"  budget    : {args.budget}")
    print(f"  operation : {rec.operation}  (~{rec.estimated_runs} runs)")
    if rec.adaptive_strategy:
        print(f"  adaptive  : {rec.adaptive_strategy}")
    for line in rec.rationale:
        print(f"  - {line}")
    for note in rec.notes:
        print(f"  Note: {note}")

    if test_path:
        cfg = load_config(config_path, strict=False)
        generate_test_scaffold(cfg, test_path, language="py")
        print(f"Wrote {test_path}")
        cfg_dict["settings"]["test_script"] = "./" + os.path.basename(test_path)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg_dict, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print()
    print("Next steps:")
    print(f"  1. Edit {config_path} — rename factors / responses to match your experiment.")
    if not test_path:
        print(f"  2. doe scaffold-test --config {config_path}")
        print(f"  3. Edit the TODO block in test.py.")
        print(f"  4. doe generate --config {config_path}")
    else:
        print(f"  2. Edit the TODO block in {test_path}.")
        print(f"  3. doe generate --config {config_path}")


def _bootstrap_factors(n_total: int, n_categorical: int) -> list[dict[str, object]]:
    """Generate placeholder factor entries for a bootstrapped config."""
    factors: list[dict[str, object]] = []
    for i in range(n_categorical):
        factors.append({
            "name": f"category_{i + 1}",
            "type": "categorical",
            "unit": "",
            "levels": ["A", "B"],
            "description": f"Categorical factor {i + 1} — replace with real levels",
        })
    for i in range(n_total - n_categorical):
        factors.append({
            "name": f"factor_{i + 1}",
            "type": "continuous",
            "unit": "",
            "levels": ["0", "1"],
            "description": f"Continuous factor {i + 1} — replace [low, high]",
        })
    return factors


def _handle_init(args: argparse.Namespace) -> None:
    """List or extract a built-in use case template, or bootstrap a fresh
    config from --factors/--budget/--goal via the suggester."""
    from importlib.resources import files as pkg_files
    import shutil

    # Bootstrap mode: --factors implies a fresh suggest-driven init.
    if args.factors is not None:
        _handle_init_bootstrap(args)
        return

    use_cases_dir = pkg_files("doe").joinpath("use_cases")

    # Discover available templates
    templates: dict[str, _TemplateInfo] = {}
    for entry in sorted(use_cases_dir.iterdir(), key=lambda p: p.name):
        config_path = entry.joinpath("config.json")
        if not config_path.is_file():
            continue
        with open(str(config_path)) as f:
            cfg = json.load(f)
        meta = cfg.get("metadata", {})
        settings = cfg.get("settings", {})
        n_factors = len(cfg.get("factors", []))
        n_responses = len(cfg.get("responses", []))
        # Strip numeric prefix for the short name (e.g. 01_reactor_optimization -> reactor_optimization)
        dir_name = entry.name
        parts = dir_name.split("_", 1)
        short_name = parts[1] if len(parts) > 1 and parts[0].isdigit() else dir_name
        templates[short_name] = {
            "dir_name": dir_name,
            "name": meta.get("name", short_name),
            "description": meta.get("description", ""),
            "operation": settings.get("operation", "?"),
            "n_factors": n_factors,
            "n_responses": n_responses,
            "path": entry,
        }

    if args.list_templates or args.template is None:
        print(f"Available templates ({len(templates)}):\n")
        print(f"{'Template':<35} {'Design':<22} {'Factors':>7} {'Name'}")
        print("-" * 100)
        for short_name, info in templates.items():
            op = info["operation"].replace("_", " ")
            print(f"{short_name:<35} {op:<22} {info['n_factors']:>7}   {info['name']}")
        print(f"\nUsage: doe init --template <name>")
        print(f"Example: doe init --template reactor_optimization")
        return

    # Find the requested template
    template_name = args.template
    if template_name not in templates:
        # Try fuzzy match: check if any template contains the search term
        matches = [k for k in templates if template_name in k]
        if len(matches) == 1:
            template_name = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous template '{args.template}'. Matches:")
            for m in matches:
                print(f"  {m}")
            return
        else:
            print(f"Unknown template '{args.template}'. Run 'doe init --list' to see available templates.")
            return

    info = templates[template_name]
    out_dir = os.path.join(args.output_dir, template_name)

    if os.path.exists(out_dir):
        print(f"Error: directory '{out_dir}' already exists.")
        return

    os.makedirs(out_dir)

    # Copy config.json and sim.sh
    src_dir = info["path"]
    for filename in ("config.json", "sim.sh", "README.md"):
        src_file = src_dir.joinpath(filename)
        if src_file.is_file():
            shutil.copy2(str(src_file), os.path.join(out_dir, filename))

    print(f"Created '{out_dir}/' from template '{template_name}'")
    print(f"  Name: {info['name']}")
    print(f"  Design: {info['operation'].replace('_', ' ')}")
    print(f"  Factors: {info['n_factors']}, Responses: {info['n_responses']}")

    # Inferred rationale: re-run the suggester against the template's
    # shape so the user sees *why* this operation fits. Stays a soft
    # commentary — we don't ask the user for a budget; we infer it from
    # the template's actual run count.
    _print_template_rationale(out_dir, info)

    print()
    print(f"Next steps:")
    print(f"  cd {out_dir}")
    print(f"  doe info --config config.json")
    print(f"  doe generate --config config.json --output results/run.sh")
    print(f"  bash results/run.sh")
    print(f"  doe analyze --config config.json")


def _print_template_rationale(out_dir: str, info: _TemplateInfo) -> None:
    """Print a 'why this design?' commentary using the suggester.

    Loads the template's config to get factor kinds + response count,
    estimates a budget by generating the design and counting runs,
    classifies the goal heuristically (screening / RSM / optimization),
    and prints the suggester's rationale alongside what the template
    actually picked. The two may differ on edge cases — that's
    informative either way.
    """
    try:
        from doe.config import load_config
        from doe.design import generate_design
        from doe.suggest import suggest
    except Exception:
        return

    cfg_path = os.path.join(out_dir, "config.json")
    if not os.path.isfile(cfg_path):
        return
    try:
        cfg = load_config(cfg_path, strict=False)
        matrix = generate_design(cfg)
    except Exception:
        return

    n_factors = len(cfg.factors)
    if n_factors == 0:
        return
    n_responses = max(1, len(cfg.responses))
    factor_kinds = [
        "categorical" if f.type == "categorical" else "continuous"
        for f in cfg.factors
    ]
    actual_runs = len(matrix.runs)

    # Goal heuristic: screening if a 2-level pure-screening op, RSM if
    # an obviously-RSM op, otherwise optimization.
    op = cfg.operation
    if op in ("plackett_burman", "fractional_factorial"):
        goal = "screening"
    elif op in (
        "central_composite", "box_behnken", "definitive_screening",
        "mixture_simplex_lattice", "mixture_simplex_centroid",
    ):
        goal = "response_surface"
    elif op in ("latin_hypercube", "d_optimal", "linear_sweep", "log_sweep"):
        goal = "optimization"
    else:
        goal = "screening"

    try:
        suggestion = suggest(
            n_factors=n_factors, n_responses=n_responses,
            budget=actual_runs, goal=goal, factor_kinds=factor_kinds,
        )
    except Exception:
        return

    print()
    print(f"  Inferred goal: {goal}")
    if suggestion.operation == op:
        print(f"  Why '{op}'?")
    else:
        print(
            f"  Note: the suggester would have picked '{suggestion.operation}' "
            f"({suggestion.estimated_runs} runs) for "
            f"{n_factors} factor(s) with budget {actual_runs}, goal '{goal}'."
        )
        print(f"  '{op}' rationale (as configured):")
    for line in suggestion.rationale:
        print(f"    - {line}")
    if suggestion.notes:
        for note in suggestion.notes:
            print(f"    Note: {note}")


def _handle_record(matrix: DesignMatrix, cfg: DOEConfig, run_arg: str) -> None:
    results_dir = cfg.out_directory
    os.makedirs(results_dir, exist_ok=True)

    if run_arg.lower() == "all":
        pending: list[ExperimentRun] = []
        for run in matrix.runs:
            result_path = os.path.join(results_dir, f"run_{run.run_id}.json")
            if not os.path.exists(result_path):
                pending.append(run)
        if not pending:
            print("All runs already have recorded results.")
            return
        print(f"Found {len(pending)} pending run(s) out of {len(matrix.runs)} total.\n")
        try:
            for run in pending:
                _record_single_run(run, matrix, cfg, results_dir)
                print()
        except KeyboardInterrupt:
            print("\nRecording interrupted. Progress saved for completed runs.")
    else:
        try:
            run_id = int(run_arg)
        except ValueError:
            print(f"Error: --run must be a number or 'all', got '{run_arg}'")
            return

        run = None
        for r in matrix.runs:
            if r.run_id == run_id:
                run = r
                break
        if run is None:
            print(f"Error: run {run_id} not found. Valid run IDs: 1-{len(matrix.runs)}")
            return

        try:
            _record_single_run(run, matrix, cfg, results_dir)
        except KeyboardInterrupt:
            print("\nRecording cancelled.")


def _record_single_run(run: ExperimentRun, matrix: DesignMatrix, cfg: DOEConfig,
                       results_dir: str) -> None:
    result_path = os.path.join(results_dir, f"run_{run.run_id}.json")

    # Check for existing results
    if os.path.exists(result_path):
        with open(result_path) as f:
            existing = json.load(f)
        print(f"Run {run.run_id} already has recorded results:")
        for k, v in existing.items():
            print(f"  {k} = {v}")
        answer = input("Overwrite? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print(f"Skipping run {run.run_id}.")
            return

    # Display factor settings
    print(f"--- Run {run.run_id} (block {run.block_id}) ---")
    print("Factor settings:")
    for name in matrix.factor_names:
        print(f"  {name} = {run.factor_values[name]}")

    # Prompt for each response
    results: dict[str, float] = {}
    for resp in cfg.responses:
        unit_str = f" ({resp.unit})" if resp.unit else ""
        while True:
            raw = input(f"  Enter {resp.name}{unit_str}: ").strip()
            try:
                value = float(raw)
                results[resp.name] = value
                break
            except ValueError:
                print(f"    Invalid number: '{raw}'. Please enter a numeric value.")

    # Save
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved -> {result_path}")


def _handle_status(matrix: DesignMatrix, cfg: DOEConfig) -> None:
    results_dir = cfg.out_directory
    total = len(matrix.runs)
    n_factors = len(matrix.factor_names)
    n_responses = len(cfg.responses)

    # Classify runs as completed or pending
    completed: list[ExperimentRun] = []
    pending: list[ExperimentRun] = []
    for run in matrix.runs:
        result_path = os.path.join(results_dir, f"run_{run.run_id}.json")
        if os.path.exists(result_path):
            completed.append(run)
        else:
            pending.append(run)

    n_done = len(completed)
    pct = int(n_done / total * 100) if total > 0 else 0

    # Header
    name = cfg.metadata.get("name", "Untitled Experiment")
    print(f"Experiment: {name}")
    print(f"Design: {matrix.operation} | {total} runs | {n_factors} factors | {n_responses} responses")
    print()

    # Progress bar
    bar_width = 20
    filled = int(bar_width * n_done / total) if total > 0 else 0
    bar = "#" * filled + "." * (bar_width - filled)
    print(f"Progress: {n_done}/{total} complete  [{bar}]  {pct}%")
    print()

    # Build a compact factor summary for a run (one line)
    def _compact_factors(run: ExperimentRun) -> str:
        parts = []
        for name in matrix.factor_names:
            parts.append(f"{name}={run.factor_values[name]}")
        return ", ".join(parts)

    if n_done == total:
        print("All runs complete!")
        print()
        print("Completed runs:")
        for run in completed:
            print(f"  Run {run.run_id}: {_compact_factors(run)}")
        print()
        print(f"Analyze results with: doe analyze --config <config>")
        return

    if n_done == 0:
        print("No runs completed yet.")
        print()
    else:
        print("Completed runs:")
        for run in completed:
            print(f"  Run {run.run_id}: {_compact_factors(run)}")
        print()

    print("Pending runs:")
    for run in pending:
        print(f"  Run {run.run_id}: {_compact_factors(run)}")
    print()

    # Next run details with units
    next_run = pending[0]
    print(f"Next run to complete: Run {next_run.run_id}")
    factor_lookup = {f.name: f for f in cfg.factors}
    for fname in matrix.factor_names:
        factor = factor_lookup[fname]
        unit_str = f" {factor.unit}" if factor.unit else ""
        print(f"  {fname} = {next_run.factor_values[fname]}{unit_str}")
    print()
    print(f"Record results with: doe record --config <config> --run {next_run.run_id}")


def _handle_export_worksheet(matrix: DesignMatrix, cfg: DOEConfig, fmt: str = "csv",
                            output_path: str | None = None) -> None:
    results_dir = cfg.out_directory
    factor_lookup = {f.name: f for f in cfg.factors}
    multiple_blocks = cast(int, matrix.metadata.get("n_blocks", 1)) > 1

    # Build column headers
    factor_headers = []
    for name in matrix.factor_names:
        factor = factor_lookup[name]
        unit_str = f" ({factor.unit})" if factor.unit else ""
        factor_headers.append(f"{name}{unit_str}")

    response_headers = []
    for resp in cfg.responses:
        unit_str = f" ({resp.unit})" if resp.unit else ""
        response_headers.append(f"{resp.name}{unit_str}")

    columns = ["Run"]
    if multiple_blocks:
        columns.append("Block")
    columns.extend(factor_headers)
    columns.extend(response_headers)
    columns.append("Notes")

    # Load existing results where available
    existing_results: dict[int, dict[str, object]] = {}
    if results_dir:
        for run in matrix.runs:
            result_path = os.path.join(results_dir, f"run_{run.run_id}.json")
            if os.path.exists(result_path):
                with open(result_path) as f:
                    existing_results[run.run_id] = json.load(f)

    # Build rows
    rows: list[list[str]] = []
    for run in matrix.runs:
        row = [str(run.run_id)]
        if multiple_blocks:
            row.append(str(run.block_id))
        for name in matrix.factor_names:
            row.append(run.factor_values[name])
        run_results = existing_results.get(run.run_id, {})
        for resp in cfg.responses:
            val = run_results.get(resp.name)
            row.append(str(val) if val is not None else "")
        row.append("")  # Notes
        rows.append(row)

    if fmt == "csv":
        output = _format_csv(columns, rows)
    else:
        output = _format_markdown_worksheet(columns, rows, matrix, cfg, multiple_blocks)

    if output_path:
        with open(output_path, "w", newline="") as f:
            f.write(output)
        print(f"Worksheet exported to {output_path}")
    else:
        print(output, end="")


def _handle_export_data(matrix: DesignMatrix, cfg: DOEConfig, fmt: str = "csv",
                       output_path: str | None = None, partial: bool = False) -> None:
    """Export design matrix with response values as a flat CSV or TSV."""
    results_dir = cfg.out_directory
    delimiter = "\t" if fmt == "tsv" else ","

    # Build headers
    columns = ["run_id", "block_id"] + list(matrix.factor_names)
    for resp in cfg.responses:
        columns.append(resp.name)

    # Load results
    results_by_run: dict[int, dict[str, object]] = {}
    missing_runs: list[int] = []
    if results_dir:
        for run in matrix.runs:
            result_path = os.path.join(results_dir, f"run_{run.run_id}.json")
            if os.path.exists(result_path):
                with open(result_path) as f:
                    results_by_run[run.run_id] = json.load(f)
            else:
                missing_runs.append(run.run_id)

    if missing_runs and not partial:
        missing_ids = ", ".join(str(r) for r in missing_runs[:10])
        suffix = f" (and {len(missing_runs) - 10} more)" if len(missing_runs) > 10 else ""
        print(f"Error: missing results for runs: {missing_ids}{suffix}", file=__import__('sys').stderr)
        print("Use --partial to include runs with missing response values.", file=__import__('sys').stderr)
        raise SystemExit(1)

    # Build rows
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    writer.writerow(columns)
    for run in matrix.runs:
        if run.run_id in missing_runs and not partial:  # pragma: no cover -
            continue  # defensive; this exact condition already raised SystemExit above
        row: list[object] = [run.run_id, run.block_id]
        for name in matrix.factor_names:
            row.append(run.factor_values[name])
        run_results = results_by_run.get(run.run_id, {})
        for resp in cfg.responses:
            val = run_results.get(resp.name)
            row.append(val if val is not None else "")
        writer.writerow(row)

    output = buf.getvalue()
    if output_path:
        with open(output_path, "w", newline="") as f:
            f.write(output)
        print(f"Data exported to {output_path} ({len(matrix.runs) - len(missing_runs)} "
              f"complete runs{', ' + str(len(missing_runs)) + ' pending' if missing_runs else ''})")
    else:
        print(output, end="")


def _format_csv(columns: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _format_markdown_worksheet(columns: list[str], rows: list[list[str]],
                              matrix: DesignMatrix, cfg: DOEConfig,
                              multiple_blocks: bool) -> str:
    lines = []

    # Header
    name = cfg.metadata.get("name", "Untitled Experiment")
    lines.append(f"# Experiment Worksheet: {name}")

    n_runs = len(matrix.runs)
    n_factors = len(matrix.factor_names)
    n_responses = len(cfg.responses)
    op_label = matrix.operation.replace("_", " ").title()
    lines.append(
        f"Design: {op_label} | {n_runs} runs | {n_factors} factors | {n_responses} responses"
    )

    if cfg.fixed_factors:
        ff_str = ", ".join(f"{k} = {v}" for k, v in cfg.fixed_factors.items())
        lines.append(f"Fixed: {ff_str}")

    lines.append("")

    # Table header
    lines.append("| " + " | ".join(columns) + " |")
    separators = []
    for col in columns:
        separators.append("-" * max(len(col), 3))
    lines.append("| " + " | ".join(separators) + " |")

    # Table rows
    for row in rows:
        padded = []
        for i, cell in enumerate(row):
            padded.append(cell.ljust(max(len(columns[i]), 3)))
        lines.append("| " + " | ".join(padded) + " |")

    lines.append("")
    lines.append("Instructions:")
    lines.append("- Fill in response columns after each run")
    lines.append("- Record any anomalies in the Notes column")
    lines.append("- Enter results with: doe record --config config.json --run <N>")
    lines.append("")

    return "\n".join(lines)


def _handle_sensitivity(matrix: DesignMatrix, cfg: DOEConfig, results_dir: str,
                       args: argparse.Namespace) -> None:
    """Sobol sensitivity on the fitted RSM, per requested response."""
    from doe.analysis import _load_all_results, _coerce_response_value
    from doe.rsm import fit_rsm
    from doe.sensitivity import sobol_indices, make_rsm_predictor, SensitivityResult
    import csv

    factor_names = matrix.factor_names
    factor_map = {f.name: f for f in cfg.factors}

    # Numeric factors with a 2-element numeric range
    numeric_names: list[str] = []
    bounds: list[tuple[float, float]] = []
    for fname in factor_names:
        f = factor_map[fname]
        if f.type not in ("continuous", "ordinal"):
            continue
        try:
            low = float(f.levels[0])
            high = float(f.levels[1])
        except (TypeError, ValueError, IndexError):
            continue
        if low == high:
            continue
        numeric_names.append(fname)
        bounds.append((min(low, high), max(low, high)))
    if not numeric_names:
        print("No numeric factors with a usable range; nothing to analyse.")
        return

    target_responses = (
        [r for r in cfg.responses if r.name == args.response]
        if args.response else list(cfg.responses)
    )
    if not target_responses:
        print(f"Response '{args.response}' not found in config.")
        return

    all_data = _load_all_results(matrix.runs, results_dir, partial=args.partial)
    n = len(matrix.runs)
    k = len(numeric_names)
    n_quad_params = 1 + 2 * k + k * (k - 1) // 2
    model_type = "quadratic" if n >= n_quad_params + 1 else "linear"

    csv_rows: list[tuple[str, str, float, float, float]] = []
    html_results: list[SensitivityResult] = []
    for resp in target_responses:
        responses: dict[int, float] = {}
        for run in matrix.runs:
            data = all_data.get(run.run_id, {})
            value = _coerce_response_value(data, resp.name, run.run_id, results_dir)
            if value is not None:
                responses[run.run_id] = value
        if len(responses) < n_quad_params + 1:
            print(f"\n=== Sensitivity: {resp.name} ===")
            print(f"  Skipped: not enough observations to fit a {model_type} surrogate.")
            continue
        valid_runs = [r for r in matrix.runs if r.run_id in responses]
        try:
            model = fit_rsm(valid_runs, responses, numeric_names,
                             [factor_map[n_] for n_ in numeric_names],
                             model_type=model_type)
        except Exception as e:
            print(f"\n=== Sensitivity: {resp.name} ===")
            print(f"  Skipped: surrogate fit failed ({e}).")
            continue

        predictor = make_rsm_predictor(model.coefficients, numeric_names, bounds)
        result = sobol_indices(
            predictor=predictor,
            factor_names=numeric_names,
            bounds=bounds,
            response_name=resp.name,
            n_base_samples=max(8, args.n_samples),
            seed=args.seed,
        )
        html_results.append(result)

        print(f"\n=== Sensitivity: {resp.name} ===")
        for note in result.notes:
            print(f"  Note: {note}")
        if not result.indices:
            continue
        print(f"  Surrogate: {model_type}, evaluations: {result.n_evaluations}")
        print(f"  {'Factor':<24} {'S_i (first order)':>18} "
              f"{'S_T (total)':>14} {'interaction':>12}")
        print(f"  {'-' * 24} {'-' * 18} {'-' * 14} {'-' * 12}")
        for entry in result.indices:
            print(f"  {entry.factor_name:<24} {entry.first_order:>18.4f} "
                  f"{entry.total_order:>14.4f} {entry.interaction_share:>12.4f}")
            csv_rows.append((
                resp.name, entry.factor_name, entry.first_order,
                entry.total_order, entry.interaction_share,
            ))

    if args.csv and csv_rows:
        os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
        with open(args.csv, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["response", "factor", "first_order", "total_order",
                              "interaction_share"])
            for row in csv_rows:
                writer.writerow(row)
        print(f"\nCSV exported: {args.csv}")
    if args.html and html_results:
        from doe.sensitivity import export_sensitivity_html
        export_sensitivity_html(html_results, args.html)
        print(f"HTML report: {args.html}")


def _handle_power(matrix: DesignMatrix, cfg: DOEConfig, args: argparse.Namespace) -> None:
    """Compute and display prospective power for each factor.

    Sigma can be supplied directly (--sigma) or estimated post-hoc from
    residuals when results are present. Either way the computation flows
    through ``doe.power.achieved_power`` so the CLI output and the
    automatic block inside ``analyze`` agree.
    """
    from doe.power import achieved_power

    n = len(matrix.runs)
    sigma = args.sigma
    delta = args.delta
    alpha = args.alpha

    if sigma is None:
        try:
            from doe.analysis import _load_all_results, _coerce_response_value
            from doe.rsm import fit_rsm
            results_dir = _resolve_results_dir(cfg, args.results_dir)
            all_data = _load_all_results(matrix.runs, results_dir, partial=args.partial)
            resp = cfg.responses[0]
            responses: dict[int, float] = {}
            for run in matrix.runs:
                data = all_data.get(run.run_id, {})
                value = _coerce_response_value(data, resp.name, run.run_id, results_dir)
                if value is not None:
                    responses[run.run_id] = value
            if responses:
                valid_runs = [r for r in matrix.runs if r.run_id in responses]
                model = fit_rsm(valid_runs, responses, matrix.factor_names, cfg.factors, model_type="linear")
                if model.diagnostics and model.diagnostics.residuals:
                    import numpy as np
                    sigma = float(np.std(model.diagnostics.residuals, ddof=1))
                    print(f"Estimated sigma from residuals: {sigma:.4f}")
        except Exception:
            pass

    if sigma is None:
        print("Error: --sigma is required when no results are available for estimation.")
        print("Usage: doe power --config FILE --sigma FLOAT [--delta FLOAT]")
        return

    df_model = sum(len(f.levels) - 1 for f in cfg.factors)
    df_error = max(1, n - 1 - df_model)
    residual_ms = sigma * sigma

    ap = achieved_power(
        matrix=matrix, factors=cfg.factors,
        residual_ms=residual_ms, df_error=df_error,
        delta=delta, alpha=alpha,
    )
    if ap is None:
        print("Cannot compute power: df_error is zero (saturated design).")
        return

    _print_achieved_power(ap, header_prefix="Power Analysis")


def _print_matrix(matrix: DesignMatrix, cfg: DOEConfig | None = None) -> None:
    if cfg and cfg.metadata.get("name"):
        print(f"Plan      : {cfg.metadata['name']}")
        if cfg.metadata.get("description"):
            print(f"Desc      : {cfg.metadata['description']}")
    print(f"Operation : {matrix.operation}")
    print(f"Factors   : {', '.join(matrix.factor_names)}")
    print(f"Base runs : {matrix.metadata.get('n_base_runs', '?')}")
    print(f"Blocks    : {matrix.metadata.get('n_blocks', '?')}")
    print(f"Total runs: {matrix.metadata.get('n_total_runs', len(matrix.runs))}")
    if cfg and cfg.responses:
        resp_str = ", ".join(
            f"{r.name} [{r.optimize}]{' (' + r.unit + ')' if r.unit else ''}"
            for r in cfg.responses
        )
        print(f"Responses : {resp_str}")
    if cfg and cfg.fixed_factors:
        ff_str = ", ".join(f"{k}={v}" for k, v in cfg.fixed_factors.items())
        print(f"Fixed     : {ff_str}")
    if matrix.metadata.get("alias_structure"):
        print(f"\nAlias Structure:")
        for alias in cast("list[object]", matrix.metadata["alias_structure"]):
            print(f"  {alias}")
    print()

    cols = ["run_id", "block_id"] + matrix.factor_names
    col_w = max(len(c) for c in cols) + 2
    header = "".join(c.ljust(col_w) for c in cols)
    print(header)
    print("-" * len(header))

    for run in matrix.runs:
        row = [str(run.run_id), str(run.block_id)] + [run.factor_values[f] for f in matrix.factor_names]
        print("".join(v.ljust(col_w) for v in row))


def _print_trend_report(report: TrendReport) -> None:
    print(f"\n=== Trend ({len(report.session_dirs)} sessions) ===")
    print(f"  Factors : {', '.join(report.factor_names)}")
    print(f"  Sessions:")
    for i, (d, n) in enumerate(zip(report.session_dirs, report.n_runs_per_session)):
        print(f"    [{i}] {d}  ({n} run(s))")
    print(f"  Matched in every session: {report.n_matched_runs} run(s)")
    for note in report.notes:
        print(f"  Note: {note}")

    for tr in report.responses:
        print(f"\n=== Response: {tr.response_name} ===")
        if tr.n_matched_runs == 0:
            for note in tr.notes:
                print(f"  {note}")
            continue

        print(f"  {'Session':<10} {'Mean':>14}")
        print(f"  {'-' * 10} {'-' * 14}")
        for i, mean in enumerate(tr.per_session_means):
            print(f"  [{i}]{'':<7} {mean:>14.4f}")

        if tr.intercept_drift_per_session == tr.intercept_drift_per_session:  # not NaN
            p_str = "—" if tr.intercept_drift_p is None else f"{tr.intercept_drift_p:.4f}"
            sig = " *" if tr.intercept_drift_p is not None and tr.intercept_drift_p < 0.05 else ""
            print(f"\n  Intercept drift / session: {tr.intercept_drift_per_session:+.4f}   p={p_str}{sig}")
        if tr.slope_drift:
            print(f"\n  Slope drift / session (change in main-effect size per session step):")
            print(f"    {'Factor':<20} {'shift/sess':>12} {'p-value':>10}")
            print(f"    {'-' * 20} {'-' * 12} {'-' * 10}")
            for e in tr.slope_drift:
                p_disp = "—" if e.p_value is None else f"{e.p_value:.4f}"
                sig = " *" if e.p_value is not None and e.p_value < 0.05 else ""
                print(f"    {e.factor_name:<20} {e.slope_drift_per_session:>+12.4f} {p_disp:>10}{sig}")
        for note in tr.notes:
            print(f"  Note: {note}")


def _print_compare_report(report: ComparisonReport) -> None:
    print(f"\n=== Compare ===")
    print(f"  Baseline : {report.baseline_dir}  ({report.n_baseline_runs} run(s))")
    print(f"  Candidate: {report.candidate_dir}  ({report.n_candidate_runs} run(s))")
    print(f"  Factors  : {', '.join(report.factor_names)}")
    print(f"  Matched  : {report.n_matched_runs} run(s)")
    for note in report.notes:
        print(f"  Note: {note}")

    for rc in report.responses:
        print(f"\n=== Response: {rc.response_name} ===")
        if rc.n_matched == 0:
            for note in rc.notes:
                print(f"  {note}")
            continue

        print(f"  Baseline mean : {rc.baseline_mean:.4f}")
        print(f"  Candidate mean: {rc.candidate_mean:.4f}   (Δ = {rc.mean_delta:+.4f})")
        if rc.paired_t_stat is not None:
            t_str = f"{rc.paired_t_stat:.3f}" if math_isfinite(rc.paired_t_stat) else "inf"
            p_str = "—" if rc.paired_p_value is None else f"{rc.paired_p_value:.4f}"
            d_str = f"{rc.cohens_d:+.3f}" if rc.cohens_d is not None and math_isfinite(rc.cohens_d) else "—"
            sig = " *" if rc.paired_p_value is not None and rc.paired_p_value < 0.05 else ""
            print(f"  Paired t-test : t={t_str}, p={p_str}, Cohen's d={d_str}{sig}")

        if rc.effect_deltas:
            any_flipped = any(e.flipped_sign for e in rc.effect_deltas)
            print(f"\n  Main-effect changes:")
            print(f"    {'Factor':<20} {'baseline':>12} {'candidate':>12} {'delta':>10}"
                  + ("  flipped" if any_flipped else ""))
            print(f"    {'-' * 20} {'-' * 12} {'-' * 12} {'-' * 10}"
                  + ("  -------" if any_flipped else ""))
            for e in rc.effect_deltas:
                flag = "  *" if e.flipped_sign else ""
                print(f"    {e.factor_name:<20} {e.baseline_effect:>12.4f} "
                      f"{e.candidate_effect:>12.4f} {e.delta:>+10.4f}{flag}")
            if any_flipped:
                print(f"    * = sign flipped between sessions")

        if rc.decomposition:
            dc = rc.decomposition
            print(f"\n  Δ decomposition (regression on pooled matched runs):")
            for note in dc.notes:
                print(f"    Note: {note}")
            if dc.df_error >= 1:
                p_str = "—" if dc.intercept_shift_p is None else f"{dc.intercept_shift_p:.4f}"
                sig = " *" if dc.intercept_shift_p is not None and dc.intercept_shift_p < 0.05 else ""
                print(f"    Intercept shift (uniform):  {dc.intercept_shift:+.4f}   p={p_str}{sig}")
                if dc.slope_shifts:
                    print(f"    {'Factor':<20} {'slope shift':>12} {'p-value':>10}")
                    print(f"    {'-' * 20} {'-' * 12} {'-' * 10}")
                    for fname, shift, p in dc.slope_shifts:
                        p_disp = "—" if p is None else f"{p:.4f}"
                        sig = " *" if p is not None and p < 0.05 else ""
                        print(f"    {fname:<20} {shift:>+12.4f} {p_disp:>10}{sig}")


def math_isfinite(x: float) -> bool:
    import math
    return math.isfinite(x) if isinstance(x, float) else True


def _print_achieved_power(ap: AchievedPower, header_prefix: str = "Achieved Power") -> None:
    print(f"\n=== {header_prefix} ===")
    print(f"  Runs: {ap.n_runs}, df_error: {ap.df_error}")
    print(f"  Sigma (sqrt residual MS): {ap.sigma:.4f}   (residual MS = {ap.residual_ms:.4f})")
    print(f"  Alpha: {ap.alpha}   |   delta: {ap.delta:.4f}   |   target power: {ap.target_power}")
    print()
    print(f"  {'Factor':<24} {'Levels':>6} {'Power @ delta':>14} {'MDE @ target':>14}")
    print(f"  {'-' * 24} {'-' * 6} {'-' * 14} {'-' * 14}")
    for entry in ap.per_factor:
        mde_str = "inf" if entry.mde_at_target == float("inf") else f"{entry.mde_at_target:.4f}"
        print(f"  {entry.factor_name:<24} {entry.n_levels:>6} "
              f"{entry.power_at_delta:>14.3f} {mde_str:>14}")
    if any(e.power_at_delta < 0.8 for e in ap.per_factor):
        print("  Note: power < 0.80 for some factors at the chosen delta.")


def _print_alias_structure(alias: AliasStructure) -> None:
    label = alias.design_type.replace("_", " ").title()
    if alias.resolution is not None:
        label += f" (Resolution {'I' * alias.resolution})"
    print(f"\n=== Alias Structure: {label} ===")
    for note in alias.notes:
        print(f"  Note: {note}")

    def _section(title: str, entries: list[AliasEntry]) -> None:
        if not entries:
            return
        any_partner = any(e.aliased_with for e in entries)
        if not any_partner:
            return
        print(f"\n  {title}")
        print(f"  {'Effect':<14}  Aliased with")
        print(f"  {'-' * 14}  {'-' * 60}")
        for e in entries:
            if not e.aliased_with:
                continue
            partners = ", ".join(
                f"{p}" + ("" if (1.0 - r) < 1e-6 else f" ({r:.2f})")
                for p, r in e.aliased_with
            )
            print(f"  {e.effect:<14}  {partners}")

    _section("Main effects", alias.main_effects)
    _section("Two-factor interactions", alias.two_factor_interactions)


def _print_report(report: AnalysisReport) -> None:
    if report.alias_structure:
        _print_alias_structure(report.alias_structure)

    for resp_name, analysis in report.results_by_response.items():
        print(f"\n=== Main Effects: {resp_name} ===")
        print(f"{'Factor':<20} {'Effect':>10} {'Std Error':>12} {'% Contribution':>16}")
        print("-" * 62)
        for e in analysis.effects:
            print(f"{e.factor_name:<20} {e.main_effect:>10.4f} {e.std_error:>12.4f} {e.pct_contribution:>15.1f}%")

        if analysis.anova_table:
            anova = analysis.anova_table
            print(f"\n=== ANOVA Table: {resp_name} ===")
            print(f"{'Source':<25} {'DF':>4} {'SS':>12} {'MS':>12} {'F':>10} {'p-value':>10}")
            print("-" * 77)
            for row in anova.rows:
                f_str = f"{row.f_value:.3f}" if row.f_value is not None else ""
                p_str = f"{row.p_value:.4f}" if row.p_value is not None else ""
                print(f"{row.source:<25} {row.df:>4} {row.ss:>12.4f} {row.ms:>12.4f} {f_str:>10} {p_str:>10}")
            if anova.lack_of_fit_row:
                lof = anova.lack_of_fit_row
                f_str = f"{lof.f_value:.3f}" if lof.f_value is not None else ""
                p_str = f"{lof.p_value:.4f}" if lof.p_value is not None else ""
                print(f"{lof.source:<25} {lof.df:>4} {lof.ss:>12.4f} {lof.ms:>12.4f} {f_str:>10} {p_str:>10}")
            if anova.pure_error_row:
                pe = anova.pure_error_row
                print(f"{pe.source:<25} {pe.df:>4} {pe.ss:>12.4f} {pe.ms:>12.4f}")
            if anova.error_row:
                err = anova.error_row
                print(f"{err.source:<25} {err.df:>4} {err.ss:>12.4f} {err.ms:>12.4f}")
            if anova.total_row:
                tot = anova.total_row
                print(f"{tot.source:<25} {tot.df:>4} {tot.ss:>12.4f} {tot.ms:>12.4f}")
            if anova.error_method == "split_plot":
                print(
                    "  Note: split-plot ANOVA — whole-plot factor is tested "
                    "against whole-plot error; all other factors and "
                    "interactions are tested against subplot error."
                )
            elif anova.error_method == "lenth":
                print("  Note: Error estimated using Lenth's pseudo-standard-error (unreplicated design)")
            elif anova.error_method == "replicates":
                print("  Note: Error term is pure error (replicated runs).")
                if anova.lack_of_fit_row and anova.lack_of_fit_row.p_value is not None:
                    p = anova.lack_of_fit_row.p_value
                    if p < 0.05:
                        print(f"        Lack-of-fit p={p:.4f} < 0.05 — the model is missing structure; consider higher-order terms.")
                    else:
                        print(f"        Lack-of-fit p={p:.4f} ≥ 0.05 — model has no detectable lack of fit.")

        if analysis.interactions:
            print(f"\n=== Interaction Effects: {resp_name} ===")
            print(f"{'Factor A':<20} {'Factor B':<20} {'Interaction':>12} {'% Contribution':>16}")
            print("-" * 72)
            for ix in analysis.interactions:
                print(f"{ix.factor_a:<20} {ix.factor_b:<20} {ix.interaction_effect:>12.4f} {ix.pct_contribution:>15.1f}%")

        print(f"\n=== Summary Statistics: {resp_name} ===")
        for factor, levels in analysis.summary_stats.items():
            print(f"\n{factor}:")
            print(f"  {'Level':<15} {'N':>5} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
            print(f"  {'-'*60}")
            for level, s in levels.items():
                print(f"  {level:<15} {s['n']:>5} {s['mean']:>10.4f} {s['std']:>10.4f} {s['min']:>10.4f} {s['max']:>10.4f}")

        if analysis.ordinal_trends:
            print(f"\n=== Ordinal Trends: {resp_name} ===")
            print(f"{'Factor':<20} {'Linear Coeff':>14} {'Lin SS':>10} {'Lin F':>10} {'Lin p':>10} {'Quad Coeff':>14} {'R² (L+Q)':>10}")
            print("-" * 102)
            for t in analysis.ordinal_trends:
                f_str = f"{t.linear_f_value:.3f}" if t.linear_f_value is not None else ""
                p_str = f"{t.linear_p_value:.4f}" if t.linear_p_value is not None else ""
                print(f"{t.factor_name:<20} {t.linear_coefficient:>14.4f} {t.linear_ss:>10.4f} {f_str:>10} {p_str:>10} {t.quadratic_coefficient:>14.4f} {t.r_squared_quadratic:>10.4f}")

        if analysis.model_adequacy:
            ma = analysis.model_adequacy
            print(f"\n=== Model Adequacy ({ma.model_type}): {resp_name} ===")
            print(f"  R²              = {ma.r_squared:.4f}")
            print(f"  Adj R²          = {ma.adj_r_squared:.4f}")
            print(f"  Predicted R²    = {ma.predicted_r_squared:.4f}   (PRESS = {ma.press:.4f})")
            if ma.shapiro_p is not None:
                flag = " ✱" if ma.shapiro_p < 0.05 else ""
                print(f"  Shapiro-Wilk    = W={ma.shapiro_w:.3f}, p={ma.shapiro_p:.3f}{flag}")
            if ma.durbin_watson is not None:
                flag = " ✱" if ma.durbin_watson < 1.0 or ma.durbin_watson > 3.0 else ""
                print(f"  Durbin-Watson   = {ma.durbin_watson:.3f}{flag}")
            if ma.runorder_drift_p is not None:
                flag = " ✱" if ma.runorder_drift_p < 0.05 else ""
                print(f"  Run-order drift = slope={ma.runorder_drift_slope:.4g}, p={ma.runorder_drift_p:.3f}{flag}")
            print(f"  Max leverage    = {ma.max_leverage:.3f}   (threshold {ma.leverage_threshold:.3f})")
            if ma.high_leverage_run_ids:
                print(f"    high-leverage runs: {ma.high_leverage_run_ids}")
            print(f"  Max Cook's D    = {ma.max_cooks_distance:.3f}   (threshold {ma.cooks_threshold:.3f})")
            if ma.high_influence_run_ids:
                print(f"    high-influence runs: {ma.high_influence_run_ids}")
            for note in ma.notes:
                print(f"  Note: {note}")

        if analysis.stationary_point:
            sp = analysis.stationary_point
            print(f"\n=== Stationary Point: {resp_name} ===")
            print(f"  Nature          : {sp.nature}"
                  f"{'' if sp.inside_design_region else '  (outside design region)'}")
            print(f"  Predicted value : {sp.predicted_value:.4f}")
            print(f"  Location        :")
            for fname in sp.factor_order:
                coded = sp.coded_location.get(fname, 0.0)
                natural = sp.natural_location.get(fname, "")
                print(f"    {fname:<18} = {natural:<14} (coded {coded:+.3f})")
            print(f"  Eigenvalues     : {', '.join(f'{v:+.4f}' for v in sp.eigenvalues)}")
            if sp.ridge_direction:
                parts = [f"{n}={v:+.3f}" for n, v in sp.ridge_direction.items()]
                print(f"  Ridge axis      : {', '.join(parts)}")

        if analysis.achieved_power:
            _print_achieved_power(analysis.achieved_power,
                                  header_prefix=f"Achieved Power: {resp_name}")

        if analysis.scheffe_model:
            sm = analysis.scheffe_model
            print(f"\n=== Scheffé Canonical ({sm.model_form}): {resp_name} ===")
            for note in sm.notes:
                print(f"  Note: {note}")
            print(f"  R² = {sm.r_squared:.4f}   Adj R² = {sm.adj_r_squared:.4f}   "
                  f"Residual MS = {sm.residual_ms:.4f}")
            print(f"  {'Term':<24} {'Coefficient':>12} {'SE':>10} {'t':>8} {'p-value':>10}")
            print(f"  {'-' * 24} {'-' * 12} {'-' * 10} {'-' * 8} {'-' * 10}")
            for term in sm.terms:
                se_str = f"{term.std_error:.4f}" if term.std_error is not None else "—"
                t_str = f"{term.t_value:.3f}" if term.t_value is not None else "—"
                p_str = f"{term.p_value:.4f}" if term.p_value is not None else "—"
                sig = " *" if term.p_value is not None and term.p_value < 0.05 else ""
                print(f"  {term.label:<24} {term.coefficient:>12.4f} {se_str:>10} "
                      f"{t_str:>8} {p_str:>10}{sig}")

        if analysis.cross_validation:
            cv = analysis.cross_validation
            print(f"\n=== Cross-Validation ({cv.model_type}, k={cv.k}): {resp_name} ===")
            for note in cv.notes:
                print(f"  Note: {note}")
            if cv.r_squared_cv == cv.r_squared_cv:  # not NaN
                print(f"  RMSE_cv = {cv.rmse:.4f}")
                print(f"  MAE_cv  = {cv.mae:.4f}")
                print(f"  R²_cv   = {cv.r_squared_cv:.4f}")

    if report.knee_point_results:
        print(f"\n=== Knee-Point / Saturation Detection ===")
        for resp_name, knees in report.knee_point_results.items():
            for k in knees:
                print(f"  {k.factor_name} -> {resp_name}: knee at {k.knee_value:.4g} "
                      f"(95% CI: [{k.ci_low:.4g}, {k.ci_high:.4g}]), "
                      f"R²={k.r_squared:.3f}, "
                      f"slopes: {k.segment1_slope:.4g} -> {k.segment2_slope:.4g}")

    for resp_name, path in report.pareto_chart_paths.items():
        print(f"\nPareto chart ({resp_name}): {path}")
    for resp_name, path in report.effects_plot_paths.items():
        print(f"Main effects ({resp_name}): {path}")
