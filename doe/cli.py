#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Design of Experiments helper tool — CLI entry point."""

import argparse
import csv
import io
import json
import os

from doe.config import load_config
from doe.design import generate_design


def _print_version():
    from doe import __version__
    print(f"doe {__version__}")
    print("Copyright (C) 2026 Martin J. Gallagher")
    print("License: GPL-3.0-or-later <https://www.gnu.org/licenses/gpl-3.0.html>")
    raise SystemExit(0)


def main():
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

    # --- analyze ---
    ana = subparsers.add_parser("analyze", help="Analyze completed experiment results")
    ana.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ana.add_argument("--results-dir", default=None, help="Override out_directory from config")
    ana.add_argument("--no-plots", action="store_true", help="Skip generating plots")
    ana.add_argument("--no-report", action="store_true", help="Skip generating the HTML report")
    ana.add_argument("--csv", default=None, metavar="DIR", help="Export analysis results to CSV files in DIR")
    ana.add_argument("--partial", action="store_true", help="Analyze only completed runs, skipping missing results")

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
    aug.add_argument("--type", required=True, choices=["fold_over", "star_points", "center_points"],
                     help="Type of augmentation")
    aug.add_argument("--output", default="run_experiments_augmented.sh", help="Output script path")
    aug.add_argument("--format", choices=["sh", "py"], default="sh", help="Script format")
    aug.add_argument("--seed", type=int, default=None, help="Random seed for run order")

    # --- init ---
    init = subparsers.add_parser("init", help="Create a new experiment from a built-in use case template")
    init.add_argument("--template", default=None, metavar="NAME",
                       help="Use case template name (e.g. reactor_optimization, coffee_brewing)")
    init.add_argument("--list", action="store_true", dest="list_templates",
                       help="List all available use case templates")
    init.add_argument("--output-dir", default=".", metavar="DIR",
                       help="Directory to extract the template into (default: current directory)")

    # --- export-worksheet ---
    ew = subparsers.add_parser("export-worksheet", help="Export design as a printable worksheet")
    ew.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ew.add_argument("--format", choices=["csv", "markdown"], default="csv", help="Output format (default: csv)")
    ew.add_argument("--output", default=None, metavar="FILE", help="Output file path (default: stdout)")
    ew.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")

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


def _dispatch(args):
    """Dispatch to the appropriate subcommand handler."""
    if args.command == "generate":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        if args.dry_run:
            _print_matrix(matrix, cfg)
        else:
            from doe.codegen import generate_script
            generate_script(matrix, cfg, args.output, format=args.format)
            print(f"Generated {len(matrix.runs)} runs -> {args.output}")
            print(f"Run with: bash {args.output}")

    elif args.command == "analyze":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        try:
            from doe.analysis import analyze
            report = analyze(matrix, cfg, results_dir=args.results_dir, no_plots=args.no_plots, partial=args.partial)
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
            generate_report(matrix, cfg, results_dir=args.results_dir, output_path=report_path, partial=args.partial)
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
        matrix = generate_design(cfg)
        try:
            _run_optimize(matrix, cfg, args)
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return

    elif args.command == "report":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        try:
            from doe.report import generate_report
            generate_report(matrix, cfg, results_dir=args.results_dir, output_path=args.output, partial=args.partial)
        except FileNotFoundError:
            _no_results_message(cfg, matrix)
            return

    elif args.command == "record":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_record(matrix, cfg, args.run)

    elif args.command == "status":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_status(matrix, cfg)

    elif args.command == "power":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        _handle_power(matrix, cfg, args)

    elif args.command == "augment":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        from doe.design import augment_design
        augmented = augment_design(matrix, cfg, augment_type=args.type)
        from doe.codegen import generate_script
        generate_script(augmented, cfg, args.output, format=args.format)
        n_new = augmented.metadata.get("n_augmented_runs", 0)
        print(f"Augmented design: {len(matrix.runs)} original + {n_new} new = {len(augmented.runs)} total runs")
        print(f"Generated -> {args.output}")

    elif args.command == "init":
        _handle_init(args)

    elif args.command == "export-worksheet":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_export_worksheet(matrix, cfg, fmt=args.format, output_path=args.output)


def _no_results_message(cfg, matrix):
    """Print a friendly message when results are missing."""
    results_dir = cfg.out_directory or "results"
    n_runs = len(matrix.runs)
    print(f"No results found in '{results_dir}/'.")
    print()
    print(f"This experiment has {n_runs} runs that need to be completed first.")
    print(f"To run the experiment:")
    print(f"  1. doe generate --config config.json --output {results_dir}/run.sh")
    print(f"  2. bash {results_dir}/run.sh")
    print()
    print(f"Or record results manually:")
    print(f"  doe record --config config.json --run 1")
    print()
    print(f"To analyze partial results (completed runs only):")
    print(f"  doe analyze --config config.json --partial")


def _run_optimize(matrix, cfg, args):
    """Run the optimize subcommand (steepest, multi, or single-response)."""
    if args.steepest:
        from doe.analysis import _load_all_results
        from doe.rsm import fit_rsm, steepest_ascent as _steepest
        results_dir = args.results_dir or cfg.out_directory or "results"
        all_data = _load_all_results(matrix.runs, results_dir, partial=args.partial)
        for resp in cfg.responses:
            responses = {}
            for run in matrix.runs:
                data = all_data.get(run.run_id, {})
                if resp.name in data:
                    responses[run.run_id] = float(data[resp.name])
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
                for fname in matrix.factor_names:
                    print(f"{pt['settings'][fname]:>14}", end="")
                print(f"{pt['predicted_value']:>14.4f}")
    elif args.multi:
        from doe.optimize import multi_objective
        multi_objective(matrix, cfg, results_dir=args.results_dir, partial=args.partial)
    else:
        from doe.optimize import recommend
        recommend(matrix, cfg, results_dir=args.results_dir, response_name=args.response, partial=args.partial)


def _handle_init(args):
    """List or extract a built-in use case template."""
    from importlib.resources import files as pkg_files
    import shutil

    use_cases_dir = pkg_files("doe").joinpath("use_cases")

    # Discover available templates
    templates = {}
    for entry in sorted(use_cases_dir.iterdir()):
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
    print()
    print(f"Next steps:")
    print(f"  cd {out_dir}")
    print(f"  doe info --config config.json")
    print(f"  doe generate --config config.json --output results/run.sh")
    print(f"  bash results/run.sh")
    print(f"  doe analyze --config config.json")


def _handle_record(matrix, cfg, run_arg):
    results_dir = cfg.out_directory
    os.makedirs(results_dir, exist_ok=True)

    if run_arg.lower() == "all":
        pending = []
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


def _record_single_run(run, matrix, cfg, results_dir):
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
    results = {}
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


def _handle_status(matrix, cfg):
    results_dir = cfg.out_directory
    total = len(matrix.runs)
    n_factors = len(matrix.factor_names)
    n_responses = len(cfg.responses)

    # Classify runs as completed or pending
    completed = []
    pending = []
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
    def _compact_factors(run):
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


def _handle_export_worksheet(matrix, cfg, fmt="csv", output_path=None):
    results_dir = cfg.out_directory
    factor_lookup = {f.name: f for f in cfg.factors}
    multiple_blocks = matrix.metadata.get("n_blocks", 1) > 1

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
    existing_results = {}
    if results_dir:
        for run in matrix.runs:
            result_path = os.path.join(results_dir, f"run_{run.run_id}.json")
            if os.path.exists(result_path):
                with open(result_path) as f:
                    existing_results[run.run_id] = json.load(f)

    # Build rows
    rows = []
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


def _format_csv(columns, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _format_markdown_worksheet(columns, rows, matrix, cfg, multiple_blocks):
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


def _handle_power(matrix, cfg, args):
    """Compute and display statistical power for each factor."""
    from scipy.stats import f as f_dist, ncf

    n = len(matrix.runs)
    n_factors = len(matrix.factor_names)

    sigma = args.sigma
    delta = args.delta
    alpha = args.alpha

    # If sigma not provided, try to estimate from results
    if sigma is None:
        try:
            from doe.analysis import _load_all_results
            from doe.rsm import fit_rsm
            results_dir = args.results_dir or cfg.out_directory or "results"
            all_data = _load_all_results(matrix.runs, results_dir, partial=args.partial)
            # Use first response to estimate sigma from residuals
            resp = cfg.responses[0]
            responses = {}
            for run in matrix.runs:
                data = all_data.get(run.run_id, {})
                if resp.name in data:
                    responses[run.run_id] = float(data[resp.name])
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

    if delta is None:
        delta = 2 * sigma  # default: detect effect of 2 sigma

    print(f"\nPower Analysis")
    print(f"  Runs: {n}, Factors: {n_factors}")
    print(f"  Sigma (error std): {sigma:.4f}")
    print(f"  Delta (min detectable effect): {delta:.4f}")
    print(f"  Alpha (significance level): {alpha}")
    print()

    # For each factor, compute power
    # Identify factor levels
    factor_level_counts = {}
    for f in cfg.factors:
        factor_level_counts[f.name] = len(f.levels)

    # Approximate df_error
    df_model = sum(factor_level_counts[f.name] - 1 for f in cfg.factors)
    df_error = max(1, n - 1 - df_model)

    f_crit = f_dist.ppf(1 - alpha, 1, df_error)

    print(f"{'Factor':<25} {'Levels':>7} {'df':>4} {'Lambda':>10} {'Power':>10}")
    print("-" * 60)

    for factor in cfg.factors:
        df_factor = len(factor.levels) - 1
        # Non-centrality parameter: lambda = n * delta^2 / (4 * sigma^2)
        # For balanced designs with r replicates per level:
        r = n // len(factor.levels)  # approx replicates per level
        ncp = r * (delta ** 2) / (sigma ** 2) if sigma > 0 else 0.0

        # Power = P(F > F_crit | H1 true) = 1 - CDF of non-central F
        power = 1.0 - ncf.cdf(f_crit, df_factor, df_error, ncp)

        print(f"{factor.name:<25} {len(factor.levels):>7} {df_factor:>4} {ncp:>10.3f} {power:>10.3f}")

    print()
    if any(1.0 - ncf.cdf(f_crit, 1, df_error, n // 2 * delta ** 2 / sigma ** 2) < 0.8 for f in cfg.factors):
        print("  Note: Power < 0.80 for some factors. Consider adding more runs or blocks.")


def _print_matrix(matrix, cfg=None):
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
        for alias in matrix.metadata["alias_structure"]:
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


def _print_report(report):
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
            if anova.error_method == "lenth":
                print("  Note: Error estimated using Lenth's pseudo-standard-error (unreplicated design)")

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

    for resp_name, path in report.pareto_chart_paths.items():
        print(f"\nPareto chart ({resp_name}): {path}")
    for resp_name, path in report.effects_plot_paths.items():
        print(f"Main effects ({resp_name}): {path}")
