#!/usr/bin/env python3
"""Design of Experiments helper tool."""

import argparse
import sys

from doe.config import load_config
from doe.design import generate_design


def main():
    parser = argparse.ArgumentParser(
        prog="doe.py",
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

    # --- info ---
    info = subparsers.add_parser("info", help="Show design info without generating anything")
    info.add_argument("--config", required=True, metavar="FILE")

    args = parser.parse_args()

    if args.command == "generate":
        cfg = load_config(args.config)
        matrix = generate_design(cfg, seed=args.seed)
        if args.dry_run:
            _print_matrix(matrix)
        else:
            from doe.codegen import generate_script
            generate_script(matrix, cfg, args.output, format=args.format)
            print(f"Generated {len(matrix.runs)} runs -> {args.output}")
            print(f"Run with: bash {args.output}")

    elif args.command == "analyze":
        cfg = load_config(args.config)
        matrix = generate_design(cfg)
        from doe.analysis import analyze
        report = analyze(matrix, cfg, results_dir=args.results_dir)
        _print_report(report)

    elif args.command == "info":
        cfg = load_config(args.config, strict=False)
        matrix = generate_design(cfg)
        _print_matrix(matrix)


def _print_matrix(matrix):
    from doe.models import DesignMatrix
    meta = matrix.metadata
    print(f"Operation : {matrix.operation}")
    print(f"Factors   : {', '.join(matrix.factor_names)}")
    print(f"Base runs : {meta.get('n_base_runs', '?')}")
    print(f"Blocks    : {meta.get('n_blocks', '?')}")
    print(f"Total runs: {meta.get('n_total_runs', len(matrix.runs))}")
    print()

    # header
    cols = ["run_id", "block_id"] + matrix.factor_names
    col_w = max(len(c) for c in cols) + 2
    header = "".join(c.ljust(col_w) for c in cols)
    print(header)
    print("-" * len(header))

    for run in matrix.runs:
        row = [str(run.run_id), str(run.block_id)] + [run.factor_values[f] for f in matrix.factor_names]
        print("".join(v.ljust(col_w) for v in row))


def _print_report(report):
    print("\n=== Main Effects ===")
    print(f"{'Factor':<20} {'Effect':>10} {'Std Error':>12} {'% Contribution':>16}")
    print("-" * 62)
    for e in report.effects:
        print(f"{e.factor_name:<20} {e.main_effect:>10.4f} {e.std_error:>12.4f} {e.pct_contribution:>15.1f}%")

    print("\n=== Summary Statistics ===")
    for factor, levels in report.summary_stats.items():
        print(f"\n{factor}:")
        print(f"  {'Level':<15} {'N':>5} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
        print(f"  {'-'*60}")
        for level, s in levels.items():
            print(f"  {level:<15} {s['n']:>5} {s['mean']:>10.4f} {s['std']:>10.4f} {s['min']:>10.4f} {s['max']:>10.4f}")

    if report.pareto_chart_path:
        print(f"\nPareto chart  : {report.pareto_chart_path}")
    if report.effects_plot_path:
        print(f"Main effects  : {report.effects_plot_path}")


if __name__ == "__main__":
    main()
