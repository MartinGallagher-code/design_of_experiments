# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""In-process coverage tests for doe/cli.py.

These tests drive ``doe.cli.main()`` directly (NOT via subprocess) so that
coverage of the CLI dispatch and handler functions is captured.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import doe.cli
from doe.config import load_config
from doe.design import generate_design


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config_dict(factors=None, responses=None, operation="full_factorial",
                 out_directory=None, extra_settings=None, metadata=None,
                 adaptive=None, fixed_factors=None):
    if factors is None:
        factors = [
            {"name": "A", "type": "continuous", "levels": ["1", "2"]},
            {"name": "B", "type": "continuous", "levels": ["10", "20"]},
        ]
    if responses is None:
        responses = [{"name": "response", "optimize": "maximize"}]
    settings = {"operation": operation, "block_count": 1, "test_script": ""}
    if out_directory is not None:
        settings["out_directory"] = out_directory
    if extra_settings:
        settings.update(extra_settings)
    cfg = {"factors": factors, "responses": responses, "settings": settings}
    if metadata is not None:
        cfg["metadata"] = metadata
    if adaptive is not None:
        cfg["adaptive"] = adaptive
    if fixed_factors is not None:
        cfg["fixed_factors"] = fixed_factors
    return cfg


def _write_config(tmp_path, cfg_dict, name="config.json"):
    path = tmp_path / name
    path.write_text(json.dumps(cfg_dict))
    return str(path)


def _write_results(results_dir, results):
    os.makedirs(results_dir, exist_ok=True)
    for run_id, data in results.items():
        with open(os.path.join(results_dir, f"run_{run_id}.json"), "w") as f:
            json.dump(data, f)


def _populate_results(cfg_path, results_dir, value_fn=None):
    """Generate the design, save the matrix, and write result files."""
    cfg = load_config(cfg_path, strict=False)
    matrix = generate_design(cfg)
    os.makedirs(results_dir, exist_ok=True)
    # Persist the matrix so analyze/report load it deterministically.
    doe.cli._save_matrix(matrix, results_dir)
    if value_fn is None:
        def value_fn(run):
            a = float(run.factor_values.get("A", 0) or 0)
            b = float(run.factor_values.get("B", 0) or 0)
            return {"response": 10.0 + 2.0 * a + 0.5 * b + run.run_id * 0.1}
    results = {run.run_id: value_fn(run) for run in matrix.runs}
    _write_results(results_dir, results)
    return cfg, matrix


def _run(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["doe"] + argv)
    doe.cli.main()


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def test_generate_dry_run(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())
    _run(monkeypatch, ["generate", "--config", cfg, "--dry-run"])
    out = capsys.readouterr().out
    assert "Operation" in out
    assert "full_factorial" in out
    assert "Total runs" in out


def test_generate_sh_output(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    output = str(tmp_path / "run.sh")
    _run(monkeypatch, ["generate", "--config", cfg, "--output", output, "--seed", "7"])
    out = capsys.readouterr().out
    assert os.path.isfile(output)
    assert "Generated" in out


def test_generate_py_output(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    output = str(tmp_path / "run.py")
    _run(monkeypatch, ["generate", "--config", cfg, "--output", output, "--format", "py"])
    assert os.path.isfile(output)


def test_generate_session_and_slurm(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    output = str(tmp_path / "run.sh")
    _run(monkeypatch, [
        "generate", "--config", cfg, "--output", output,
        "--session", "exp", "--executor", "slurm",
        "--slurm-partition", "short", "--slurm-time", "00:10:00",
        "--slurm-cpus-per-task", "2", "--slurm-mem", "4G",
        "--slurm-max-concurrent", "3",
    ])
    out = capsys.readouterr().out
    assert os.path.isfile(output)
    assert "session" in out.lower()


def test_generate_replicate_center_and_resolution(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "2"]},
        {"name": "B", "type": "continuous", "levels": ["10", "20"]},
        {"name": "C", "type": "continuous", "levels": ["5", "9"]},
        {"name": "D", "type": "continuous", "levels": ["0", "4"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="fractional_factorial", out_directory=out_dir))
    _run(monkeypatch, [
        "generate", "--config", cfg, "--dry-run",
        "--resolution", "4", "--replicate-center", "2",
    ])
    out = capsys.readouterr().out
    assert "Operation" in out


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

def test_info(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict(
        metadata={"name": "My Plan", "description": "desc"}))
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Operation" in out
    assert "My Plan" in out


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

def test_analyze_full(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    csv_dir = str(tmp_path / "csv")
    _run(monkeypatch, [
        "analyze", "--config", cfg, "--results-dir", out_dir,
        "--no-plots", "--csv", csv_dir,
    ])
    out = capsys.readouterr().out
    assert "Main Effects" in out
    assert "Summary Statistics" in out
    assert "CSV exported" in out
    assert "HTML report" in out


def test_analyze_no_report_knee_norsm(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, [
        "analyze", "--config", cfg, "--results-dir", out_dir,
        "--no-plots", "--no-report", "--knee", "--no-rsm",
    ])
    out = capsys.readouterr().out
    assert "Main Effects" in out


def test_analyze_partial_and_filter(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj, matrix = _populate_results(cfg, out_dir)
    # Remove one result to exercise --partial.
    first = matrix.runs[0].run_id
    os.remove(os.path.join(out_dir, f"run_{first}.json"))
    _run(monkeypatch, [
        "analyze", "--config", cfg, "--results-dir", out_dir,
        "--no-plots", "--no-report", "--partial",
        "--filter-runs", str(matrix.runs[-1].run_id),
    ])
    out = capsys.readouterr().out
    assert "excluded run IDs" in out


def test_analyze_no_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _run(monkeypatch, ["analyze", "--config", cfg, "--results-dir", out_dir,
                       "--no-plots", "--no-report"])
    out = capsys.readouterr().out
    assert "No results found" in out


# ---------------------------------------------------------------------------
# optimize
# ---------------------------------------------------------------------------

def test_optimize_single(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["optimize", "--config", cfg, "--results-dir", out_dir])
    capsys.readouterr()


def test_optimize_multi(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    responses = [
        {"name": "r1", "optimize": "maximize"},
        {"name": "r2", "optimize": "minimize"},
    ]
    cfg = _write_config(tmp_path, _config_dict(responses=responses, out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _write_results(out_dir, {
        run.run_id: {"r1": 10.0 + run.run_id, "r2": 5.0 - run.run_id * 0.1}
        for run in matrix.runs})
    _run(monkeypatch, ["optimize", "--config", cfg, "--results-dir", out_dir, "--multi"])
    capsys.readouterr()


def test_optimize_steepest(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["optimize", "--config", cfg, "--results-dir", out_dir, "--steepest"])
    out = capsys.readouterr().out
    assert "Steepest" in out


def test_optimize_no_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _run(monkeypatch, ["optimize", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "No results found" in out


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def test_report(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    output = str(tmp_path / "report.html")
    _run(monkeypatch, ["report", "--config", cfg, "--results-dir", out_dir,
                       "--output", output])
    assert os.path.isfile(output)


def test_report_no_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    output = str(tmp_path / "report.html")
    _run(monkeypatch, ["report", "--config", cfg, "--results-dir", out_dir,
                       "--output", output])
    out = capsys.readouterr().out
    assert "No results found" in out


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def test_status_no_runs(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["status", "--config", cfg])
    out = capsys.readouterr().out
    assert "No runs completed yet" in out
    assert "Pending runs" in out


def test_status_partial(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj, matrix = _populate_results(cfg, out_dir)
    os.remove(os.path.join(out_dir, f"run_{matrix.runs[-1].run_id}.json"))
    _run(monkeypatch, ["status", "--config", cfg])
    out = capsys.readouterr().out
    assert "Completed runs" in out
    assert "Next run to complete" in out


def test_status_all_complete(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["status", "--config", cfg])
    out = capsys.readouterr().out
    assert "All runs complete" in out


# ---------------------------------------------------------------------------
# record (interactive — monkeypatch input)
# ---------------------------------------------------------------------------

def test_record_single(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "42.0")
    _run(monkeypatch, ["record", "--config", cfg, "--run", "1"])
    out = capsys.readouterr().out
    assert "Saved" in out
    assert os.path.isfile(os.path.join(out_dir, "run_1.json"))


def test_record_bad_run(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["record", "--config", cfg, "--run", "notanumber"])
    out = capsys.readouterr().out
    assert "must be a number" in out


def test_record_run_not_found(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["record", "--config", cfg, "--run", "9999"])
    out = capsys.readouterr().out
    assert "not found" in out


def test_record_all(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "1.5")
    _run(monkeypatch, ["record", "--config", cfg, "--run", "all"])
    out = capsys.readouterr().out
    assert "pending run" in out


def test_record_all_none_pending(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["record", "--config", cfg, "--run", "all"])
    out = capsys.readouterr().out
    assert "already have recorded results" in out


# ---------------------------------------------------------------------------
# power
# ---------------------------------------------------------------------------

def test_power_with_sigma(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["power", "--config", cfg, "--sigma", "1.0", "--delta", "2.0"])
    out = capsys.readouterr().out
    assert "Power Analysis" in out


def test_power_estimated_sigma(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["power", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "Power" in out or "Estimated sigma" in out


def test_power_no_sigma_no_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["power", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "sigma is required" in out


# ---------------------------------------------------------------------------
# augment
# ---------------------------------------------------------------------------

def test_augment(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="fractional_factorial", out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    output = str(tmp_path / "aug.sh")
    _run(monkeypatch, ["augment", "--config", cfg, "--type", "fold_over",
                       "--output", output])
    out = capsys.readouterr().out
    assert "Augmented design" in out
    assert os.path.isfile(output)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def test_init_list(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["init", "--list"])
    out = capsys.readouterr().out
    assert "Available templates" in out


def test_init_template(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "extracted")
    os.makedirs(out_dir, exist_ok=True)
    # Discover a real template name from the list output.
    _run(monkeypatch, ["init", "--list"])
    listing = capsys.readouterr().out
    # Pick the first template name token from the table.
    name = None
    for line in listing.splitlines():
        line = line.strip()
        if not line or line.startswith(("Available", "Template", "-", "Usage", "Example")):
            continue
        name = line.split()[0]
        break
    assert name is not None
    _run(monkeypatch, ["init", "--template", name, "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "Created" in out or "from template" in out


def test_init_unknown_template(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["init", "--template", "definitely_not_a_template_xyz",
                       "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Unknown template" in out


def test_init_bootstrap(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "boot")
    _run(monkeypatch, ["init", "--factors", "3", "--budget", "16",
                       "--goal", "screening", "--output-dir", out_dir,
                       "--with-test"])
    out = capsys.readouterr().out
    assert "Wrote" in out
    assert os.path.isfile(os.path.join(out_dir, "config.json"))


def test_init_bootstrap_no_budget(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "boot")
    _run(monkeypatch, ["init", "--factors", "3", "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "budget is required" in out


def test_init_bootstrap_bad_categorical(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "boot")
    _run(monkeypatch, ["init", "--factors", "2", "--budget", "8",
                       "--categorical", "5", "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "categorical" in out


# ---------------------------------------------------------------------------
# export-worksheet
# ---------------------------------------------------------------------------

def test_export_worksheet_csv_stdout(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["export-worksheet", "--config", cfg, "--format", "csv"])
    out = capsys.readouterr().out
    assert "Run" in out


def test_export_worksheet_markdown_file(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    output = str(tmp_path / "ws.md")
    _run(monkeypatch, ["export-worksheet", "--config", cfg, "--format",
                       "markdown", "--output", output])
    out = capsys.readouterr().out
    assert "exported" in out
    assert os.path.isfile(output)


# ---------------------------------------------------------------------------
# export-data
# ---------------------------------------------------------------------------

def test_export_data_csv(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["export-data", "--config", cfg, "--format", "csv"])
    out = capsys.readouterr().out
    assert "run_id" in out


def test_export_data_tsv_file(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    output = str(tmp_path / "data.tsv")
    _run(monkeypatch, ["export-data", "--config", cfg, "--format", "tsv",
                       "--output", output])
    out = capsys.readouterr().out
    assert "exported" in out
    assert os.path.isfile(output)


def test_export_data_missing_no_partial(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["export-data", "--config", cfg, "--format", "csv"])
    err = capsys.readouterr().err
    assert "missing results" in err


def test_export_data_partial(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj, matrix = _populate_results(cfg, out_dir)
    os.remove(os.path.join(out_dir, f"run_{matrix.runs[0].run_id}.json"))
    _run(monkeypatch, ["export-data", "--config", cfg, "--partial"])
    out = capsys.readouterr().out
    assert "run_id" in out


# ---------------------------------------------------------------------------
# suggest
# ---------------------------------------------------------------------------

def test_suggest(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["suggest", "--factors", "4", "--budget", "16",
                       "--goal", "response_surface"])
    out = capsys.readouterr().out
    assert "Suggestion" in out
    assert "operation" in out


def test_suggest_categorical(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["suggest", "--factors", "3", "--budget", "20",
                       "--categorical", "1", "--goal", "screening"])
    out = capsys.readouterr().out
    assert "Suggestion" in out


# ---------------------------------------------------------------------------
# sensitivity
# ---------------------------------------------------------------------------

def test_sensitivity(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir))
    _populate_results(cfg, out_dir)
    csv_out = str(tmp_path / "sobol.csv")
    html_out = str(tmp_path / "sobol.html")
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir,
                       "--n-samples", "16", "--csv", csv_out, "--html", html_out])
    out = capsys.readouterr().out
    assert "Sensitivity" in out


def test_sensitivity_no_numeric(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "categorical", "levels": ["x", "y"]},
        {"name": "B", "type": "categorical", "levels": ["p", "q"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(factors=factors, out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "No numeric factors" in out


# ---------------------------------------------------------------------------
# compare / trend
# ---------------------------------------------------------------------------

def _two_sessions(tmp_path, cfg_path):
    cfg_obj = load_config(cfg_path, strict=False)
    matrix = generate_design(cfg_obj)
    base = str(tmp_path / "baseline")
    cand = str(tmp_path / "candidate")
    for d, bump in ((base, 0.0), (cand, 3.0)):
        os.makedirs(d, exist_ok=True)
        doe.cli._save_matrix(matrix, d)
        _write_results(d, {
            run.run_id: {"response": 10.0 + run.run_id * 0.5 + bump}
            for run in matrix.runs})
    return base, cand


def test_compare(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())
    base, cand = _two_sessions(tmp_path, cfg)
    csv_dir = str(tmp_path / "cmpcsv")
    html = str(tmp_path / "cmp.html")
    _run(monkeypatch, ["compare", "--config", cfg, "--baseline", base,
                       "--candidate", cand, "--csv", csv_dir, "--html", html])
    out = capsys.readouterr().out
    assert "Compare" in out


def test_trend(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    sessions = []
    for i in range(3):
        d = str(tmp_path / f"sess{i}")
        os.makedirs(d, exist_ok=True)
        doe.cli._save_matrix(matrix, d)
        _write_results(d, {
            run.run_id: {"response": 10.0 + run.run_id * 0.5 + i * 2.0}
            for run in matrix.runs})
        sessions.append(d)
    csv_dir = str(tmp_path / "trendcsv")
    html = str(tmp_path / "trend.html")
    _run(monkeypatch, ["trend", "--config", cfg, "--sessions"] + sessions +
                      ["--csv", csv_dir, "--html", html])
    out = capsys.readouterr().out
    assert "Trend" in out


# ---------------------------------------------------------------------------
# archive
# ---------------------------------------------------------------------------

def test_archive(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    _populate_results(cfg, out_dir)
    output = str(tmp_path / "archive.tar.gz")
    _run(monkeypatch, ["archive", "--session", out_dir, "--output", output,
                       "--config", cfg])
    out = capsys.readouterr().out
    assert "Wrote archive" in out
    assert os.path.isfile(output)


# ---------------------------------------------------------------------------
# calibrate / simulate
# ---------------------------------------------------------------------------

def test_simulate(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    # A simulator module.
    sim_py = tmp_path / "sim_mod.py"
    sim_py.write_text(
        "def run(factors):\n"
        "    a = float(factors.get('A', 0) or 0)\n"
        "    b = float(factors.get('B', 0) or 0)\n"
        "    return {'response': a + b}\n"
    )
    target = f"{sim_py}:run"
    _run(monkeypatch, ["simulate", "--config", cfg, "--func", target,
                       "--results-dir", out_dir])
    capsys.readouterr()
    assert os.path.isfile(os.path.join(out_dir, f"run_{matrix.runs[0].run_id}.json"))


def test_calibrate(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(factors=factors, out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    observed = str(tmp_path / "observed")
    os.makedirs(observed, exist_ok=True)
    doe.cli._save_matrix(matrix, observed)
    _write_results(observed, {
        run.run_id: {"response": 2.0 * float(run.factor_values["A"])
                     + 1.0 * float(run.factor_values["B"])}
        for run in matrix.runs})
    sim_py = tmp_path / "model.py"
    sim_py.write_text(
        "def model(factors, k1, k2):\n"
        "    a = float(factors.get('A', 0) or 0)\n"
        "    b = float(factors.get('B', 0) or 0)\n"
        "    return {'response': k1 * a + k2 * b}\n"
    )
    report = str(tmp_path / "cal.json")
    _run(monkeypatch, ["calibrate", "--config", cfg, "--func", f"{sim_py}:model",
                       "--params", "k1:0.5:1:3", "k2:0.5:0:2",
                       "--observed", observed, "--report", report])
    out = capsys.readouterr().out
    assert "Calibration" in out


# ---------------------------------------------------------------------------
# serve (FileNotFoundError path only — no real server)
# ---------------------------------------------------------------------------

def test_serve_bad_root(tmp_path, monkeypatch, capsys):
    bad = str(tmp_path / "does_not_exist")
    _run(monkeypatch, ["serve", "--root", bad])
    out = capsys.readouterr().out
    assert "Error" in out


# ---------------------------------------------------------------------------
# next-batch
# ---------------------------------------------------------------------------

def test_next_batch(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir,
        adaptive={"strategy": "explore", "batch_size": 2, "stopping_max_phases": 5}))
    _populate_results(cfg, out_dir)
    output = str(tmp_path / "next.sh")
    _run(monkeypatch, ["next-batch", "--config", cfg, "--results-dir", out_dir,
                       "--strategy", "explore", "--batch-size", "2",
                       "--output", output])
    out = capsys.readouterr().out
    assert "Phase" in out or "Stopping" in out


def test_next_batch_no_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(
        out_directory=out_dir,
        adaptive={"strategy": "explore", "batch_size": 2}))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["next-batch", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "No results found" in out


# ---------------------------------------------------------------------------
# scaffold-config / scaffold-test
# ---------------------------------------------------------------------------

def test_scaffold_config(tmp_path, monkeypatch, capsys):
    output = str(tmp_path / "newcfg.json")
    _run(monkeypatch, ["scaffold-config", "--output", output])
    out = capsys.readouterr().out
    assert "Wrote starter config" in out
    assert os.path.isfile(output)
    # Second run without --force should warn.
    _run(monkeypatch, ["scaffold-config", "--output", output])
    out = capsys.readouterr().out
    assert "already exists" in out


def test_scaffold_test(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    output = str(tmp_path / "test.py")
    _run(monkeypatch, ["scaffold-test", "--config", cfg, "--output", output])
    out = capsys.readouterr().out
    assert "Wrote test scaffold" in out
    assert os.path.isfile(output)


# ---------------------------------------------------------------------------
# version / no command / error paths
# ---------------------------------------------------------------------------

def test_version(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["--version"])
    out = capsys.readouterr().out
    assert "doe" in out


def test_no_command_prints_help(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _run(monkeypatch, [])
    out = capsys.readouterr().out
    assert "usage" in out.lower()


def test_missing_config_file(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["info", "--config", str(tmp_path / "nope.json")])
    out = capsys.readouterr().out
    assert "Error" in out


def test_bad_operation(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict(operation="not_a_real_operation"))
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Error" in out


def test_invalid_json_config(tmp_path, monkeypatch, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{ this is not valid json ")
    _run(monkeypatch, ["info", "--config", str(path)])
    out = capsys.readouterr().out
    assert "Error" in out
