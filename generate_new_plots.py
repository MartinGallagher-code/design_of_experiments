#!/usr/bin/env python3
"""Generate new plot types (normal, half-normal, diagnostics) for all use cases
and copy them to website/images/ with the correct naming convention."""

import glob
import os
import shutil
import sys

def generate_plots_for_use_case(uc_dir):
    """Run analysis with plots for a single use case, generating new plot types."""
    config_path = os.path.join(uc_dir, "config.json")
    results_dir = os.path.join(uc_dir, "results")

    if not os.path.exists(config_path) or not os.path.isdir(results_dir):
        return []

    # Check there are result files
    result_files = glob.glob(os.path.join(results_dir, "run_*.json"))
    if not result_files:
        return []

    try:
        from doe.config import load_config
        from doe.design import generate_design
        from doe.analysis import analyze

        cfg = load_config(config_path)
        matrix = generate_design(cfg)

        # Set processed_directory to results/analysis
        analysis_dir = os.path.join(results_dir, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        cfg.processed_directory = analysis_dir

        # Run analysis with plots enabled
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=False, partial=True)

        # Collect all new plot paths
        new_plots = []
        for paths_dict in [report.normal_plot_paths, report.half_normal_plot_paths, report.diagnostics_plot_paths]:
            for resp_name, path in paths_dict.items():
                if os.path.exists(path):
                    new_plots.append(path)

        return new_plots

    except Exception as e:
        print(f"  Warning: {uc_dir}: {e}", file=sys.stderr)
        return []


def copy_plots_to_website(uc_dir, plots):
    """Copy generated plots to website/images/ with proper naming convention."""
    # Extract use case number from directory name
    basename = os.path.basename(uc_dir)
    parts = basename.split("_", 1)
    if not parts[0].isdigit():
        return 0

    num = int(parts[0])
    prefix = f"{num:02d}" if num < 100 else str(num)

    copied = 0
    for plot_path in plots:
        filename = os.path.basename(plot_path)
        # Rename: normal_effects_yield.png -> 01_normal_effects_yield.png
        dest = os.path.join("website", "images", f"{prefix}_{filename}")
        shutil.copy2(plot_path, dest)
        copied += 1

    return copied


def main():
    # Find all use case directories
    uc_dirs = sorted(glob.glob("doe/use_cases/*/"))
    total_new = 0

    for uc_dir in uc_dirs:
        uc_dir = uc_dir.rstrip("/")
        basename = os.path.basename(uc_dir)
        parts = basename.split("_", 1)
        if not parts[0].isdigit():
            continue

        num = int(parts[0])
        sys.stdout.write(f"  [{num:3d}] {basename}...")
        sys.stdout.flush()

        plots = generate_plots_for_use_case(uc_dir)
        if plots:
            copied = copy_plots_to_website(uc_dir, plots)
            total_new += copied
            print(f" {copied} new plots")
        else:
            print(f" no new plots")

    print(f"\nTotal new plots generated: {total_new}")


if __name__ == "__main__":
    # Suppress matplotlib GUI
    import matplotlib
    matplotlib.use("Agg")

    print("Generating new plots (normal, half-normal, diagnostics) for all use cases...")
    main()
