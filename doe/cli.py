#!/usr/bin/env python3
"""Design of Experiments helper tool — CLI entry point."""

import argparse
import csv
import io
import json
import os

from doe.config import load_config
from doe.design import generate_design


def main():
    parser = argparse.ArgumentParser(
        prog="doe",
        description="Design of Experiments (DOE) helper tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    # --- export-worksheet ---
    ew = subparsers.add_parser("export-worksheet", help="Export design as a printable worksheet")
    ew.add_argument("--config", required=True, metavar="FILE", help="Input JSON config file")
    ew.add_argument("--format", choices=["csv", "markdown"], default="csv", help="Output format (default: csv)")
    ew.add_argument("--output", default=None, metavar="FILE", help="Output file path (default: stdout)")
    ew.add_argument("--seed", type=int, default=42, help="Random seed for run order (default: 42)")

    args = parser.parse_args()

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
        from doe.analysis import analyze
        report = analyze(matrix, cfg, results_dir=args.results_dir, no_plots=args.no_plots, partial=args.partial)
        _print_report(report)
        if args.csv:
            from doe.analysis import export_csv
            csv_files = export_csv(report, args.csv)
            for p in csv_files:
                print(f"CSV exported: {p}")

    elif args.command == "info":
        cfg = load_config(args.config, strict=False)
        matrix = generate_design(cfg)
        _print_matrix(matrix, cfg)

    elif args.command == "optimize":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        if args.multi:
            from doe.optimize import multi_objective
            multi_objective(matrix, cfg, results_dir=args.results_dir, partial=args.partial)
        else:
            from doe.optimize import recommend
            recommend(matrix, cfg, results_dir=args.results_dir, response_name=args.response, partial=args.partial)

    elif args.command == "report":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        from doe.report import generate_report
        generate_report(matrix, cfg, results_dir=args.results_dir, output_path=args.output, partial=args.partial)

    elif args.command == "record":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_record(matrix, cfg, args.run)

    elif args.command == "status":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_status(matrix, cfg)

    elif args.command == "export-worksheet":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        _handle_export_worksheet(matrix, cfg, fmt=args.format, output_path=args.output)


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
        print(f"Analyze results with: python doe.py analyze --config <config>")
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
    print(f"Record results with: python doe.py record --config <config> --run {next_run.run_id}")


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
    lines.append("- Enter results with: python doe.py record --config config.json --run <N>")
    lines.append("")

    return "\n".join(lines)


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
