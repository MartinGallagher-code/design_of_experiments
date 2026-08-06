# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Supplementary line-coverage tests for ``doe/cli.py``.

These target the error branches, optional-print branches, and report
formatting paths that the primary ``test_cli_coverage.py`` suite does not
reach. Tests drive ``doe.cli.main()`` in-process where possible; a handful
call the module-level helper functions (``_print_report``,
``_print_matrix``, ``_resolve_results_dir``, ``_print_template_rationale``)
directly to exercise pure formatting/error branches deterministically.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import doe.cli
import doe.config
import doe.design
import doe.power
import doe.rsm
import doe.suggest
import doe.adaptive
from doe.config import load_config
from doe.design import generate_design
from doe.suggest import Suggestion
from doe.models import (
    AnalysisReport,
    AnovaRow,
    AnovaTable,
    AliasEntry,
    AliasStructure,
    DesignMatrix,
    EffectResult,
    InteractionEffect,
    ModelAdequacy,
    OrdinalTrendResult,
    ResponseAnalysis,
    StationaryPoint,
)
from doe.mixture import ScheffeModel, ScheffeTerm


# ---------------------------------------------------------------------------
# Helpers (mirrors test_cli_coverage.py conventions)
# ---------------------------------------------------------------------------

def _config_dict(factors=None, responses=None, operation="full_factorial",
                 out_directory=None, extra_settings=None, metadata=None,
                 adaptive=None, fixed_factors=None, block_count=1):
    if factors is None:
        factors = [
            {"name": "A", "type": "continuous", "levels": ["1", "2"]},
            {"name": "B", "type": "continuous", "levels": ["10", "20"]},
        ]
    if responses is None:
        responses = [{"name": "response", "optimize": "maximize"}]
    settings = {"operation": operation, "block_count": block_count,
                "test_script": ""}
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
    cfg = load_config(cfg_path, strict=False)
    matrix = generate_design(cfg)
    os.makedirs(results_dir, exist_ok=True)
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
# _resolve_results_dir  (lines 121-122, 125)
# ---------------------------------------------------------------------------

def test_resolve_results_dir_no_symlink_returns_base(tmp_path):
    """No <out>/latest symlink -> return the base directory (line 125)."""
    base = str(tmp_path / "results")
    os.makedirs(base, exist_ok=True)
    cfg_path = _write_config(tmp_path, _config_dict(out_directory=base))
    cfg = load_config(cfg_path, strict=False)
    assert doe.cli._resolve_results_dir(cfg, None) == base


def test_resolve_results_dir_readlink_oserror(tmp_path, monkeypatch, capsys):
    """A latest symlink whose readlink() fails -> target='' (lines 121-122)."""
    base = tmp_path / "results"
    base.mkdir()
    target = base / "session-1"
    target.mkdir()
    latest = base / "latest"
    latest.symlink_to(target)
    cfg_path = _write_config(tmp_path, _config_dict(out_directory=str(base)))
    cfg = load_config(cfg_path, strict=False)

    def _boom(path):
        raise OSError("cannot read link")

    monkeypatch.setattr(os, "readlink", _boom)
    resolved = doe.cli._resolve_results_dir(cfg, None)
    assert resolved == str(latest)
    out = capsys.readouterr().out
    assert "Using latest session" in out


# ---------------------------------------------------------------------------
# main() top-level exception handling  (lines 507, 509-512)
# ---------------------------------------------------------------------------

def test_main_permission_error(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())

    def _raise(*a, **k):
        raise PermissionError("permission denied")

    monkeypatch.setattr(doe.cli, "load_config", _raise)
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Error" in out and "permission denied" in out


def test_main_oserror_no_such_file(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())

    def _raise(*a, **k):
        raise OSError("No such file or directory: 'x'")

    monkeypatch.setattr(doe.cli, "load_config", _raise)
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Error" in out


def test_main_oserror_other_reraises(tmp_path, monkeypatch):
    cfg = _write_config(tmp_path, _config_dict())

    def _raise(*a, **k):
        raise OSError("disk exploded")

    monkeypatch.setattr(doe.cli, "load_config", _raise)
    with pytest.raises(OSError):
        _run(monkeypatch, ["info", "--config", cfg])


# ---------------------------------------------------------------------------
# info: evaluate_design failure is swallowed  (lines 590-591)
# ---------------------------------------------------------------------------

def test_info_evaluate_design_raises(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())

    def _boom(*a, **k):
        raise RuntimeError("metrics failed")

    monkeypatch.setattr(doe.design, "evaluate_design", _boom)
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Operation" in out  # matrix still printed; metrics silently skipped


# ---------------------------------------------------------------------------
# suggest: all optional print branches  (669, 671, 675, 679, 687, 689, 694)
# ---------------------------------------------------------------------------

def test_suggest_all_optional_fields(monkeypatch, capsys):
    """Force a fully-populated Suggestion so every optional print fires."""
    full = Suggestion(
        operation="custom_op",
        estimated_runs=10,
        rationale=["reason one"],
        block_count=2,
        replicate_center=3,
        min_resolution=4,
        adaptive_strategy="bayesian",
        notes=["a note"],
    )
    monkeypatch.setattr(doe.suggest, "suggest", lambda **kw: full)
    _run(monkeypatch, ["suggest", "--factors", "4", "--budget", "16"])
    out = capsys.readouterr().out
    assert "block_count" in out
    assert "replicate_center" in out
    assert "adaptive.strategy" in out
    assert "Note: a note" in out
    assert '"block_count": 2' in out
    assert '"adaptive"' in out


# ---------------------------------------------------------------------------
# scaffold-test: refuse to overwrite  (lines 817-821)
# ---------------------------------------------------------------------------

def test_scaffold_test_exists_no_force(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict())
    output = tmp_path / "test.py"
    output.write_text("# existing\n")
    _run(monkeypatch, ["scaffold-test", "--config", cfg, "--output", str(output)])
    out = capsys.readouterr().out
    assert "already exists" in out


# ---------------------------------------------------------------------------
# next-batch: stop recommended  (lines 851-852)
# ---------------------------------------------------------------------------

def test_next_batch_should_stop(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(
        out_directory=out_dir,
        adaptive={"strategy": "explore", "batch_size": 2}))
    _populate_results(cfg, out_dir)
    state = SimpleNamespace(should_stop=True, stop_reason="converged",
                            phase=3, total_runs=20)
    monkeypatch.setattr(doe.adaptive, "plan_next_batch",
                        lambda *a, **k: (None, state))
    _run(monkeypatch, ["next-batch", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "Stopping recommended: converged" in out
    assert "total runs" in out


# ---------------------------------------------------------------------------
# _no_results_message: test_script configured branch  (lines 879-880)
# ---------------------------------------------------------------------------

def test_no_results_message_with_test_script(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(
        out_directory=out_dir,
        extra_settings={"test_script": "./sim.py"}))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["analyze", "--config", cfg, "--results-dir", out_dir,
                       "--no-plots", "--no-report"])
    out = capsys.readouterr().out
    assert "No results found" in out
    assert "run.sh" in out


# ---------------------------------------------------------------------------
# optimize --steepest: response with no data is skipped  (line 904)
# ---------------------------------------------------------------------------

def test_optimize_steepest_response_no_data(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    responses = [
        {"name": "r1", "optimize": "maximize"},
        {"name": "r2", "optimize": "maximize"},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, responses=responses,
        operation="central_composite", out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    # Only r1 has data; r2 has none -> steepest skips it (continue).
    _write_results(out_dir, {
        run.run_id: {"r1": 1.0 + 2.0 * float(run.factor_values["A"])
                     + float(run.factor_values["B"])}
        for run in matrix.runs})
    _run(monkeypatch, ["optimize", "--config", cfg, "--results-dir", out_dir,
                       "--steepest"])
    out = capsys.readouterr().out
    assert "Steepest" in out  # r1 produced output; r2 was skipped


# ---------------------------------------------------------------------------
# init bootstrap validation branches  (938-939, 960-961)
# ---------------------------------------------------------------------------

def test_init_bootstrap_nonpositive_factors(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "boot")
    _run(monkeypatch, ["init", "--factors", "0", "--budget", "8",
                       "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "must both be positive" in out


def test_init_bootstrap_test_exists(tmp_path, monkeypatch, capsys):
    out_dir = tmp_path / "boot"
    out_dir.mkdir()
    (out_dir / "test.py").write_text("# already here\n")
    _run(monkeypatch, ["init", "--factors", "2", "--budget", "8",
                       "--with-test", "--output-dir", str(out_dir)])
    out = capsys.readouterr().out
    assert "test.py" in out and "already exists" in out


# ---------------------------------------------------------------------------
# init bootstrap: block_count / adaptive overlay  (991, 993-999, 1025)
# ---------------------------------------------------------------------------

def test_init_bootstrap_block_and_adaptive(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "boot")
    rec = Suggestion(
        operation="central_composite",
        estimated_runs=20,
        rationale=["reason"],
        block_count=2,
        replicate_center=3,
        min_resolution=5,
        adaptive_strategy="bayesian",
        notes=["note"],
    )
    monkeypatch.setattr(doe.suggest, "suggest", lambda **kw: rec)
    _run(monkeypatch, ["init", "--factors", "3", "--budget", "20",
                       "--goal", "optimization", "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "adaptive  : bayesian" in out
    with open(os.path.join(out_dir, "config.json")) as f:
        written = json.load(f)
    assert written["settings"]["block_count"] == 2
    assert written["adaptive"]["strategy"] == "bayesian"


# ---------------------------------------------------------------------------
# init template: fuzzy match / ambiguous / dir-exists  (1130, 1132-1135, 1144-1145)
# ---------------------------------------------------------------------------

def test_init_template_fuzzy_single(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "out")
    os.makedirs(out_dir, exist_ok=True)
    _run(monkeypatch, ["init", "--template", "reactor", "--output-dir", out_dir])
    out = capsys.readouterr().out
    assert "reactor_optimization" in out


def test_init_template_ambiguous(tmp_path, monkeypatch, capsys):
    _run(monkeypatch, ["init", "--template", "wood", "--output-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Ambiguous template" in out


def test_init_template_dir_exists(tmp_path, monkeypatch, capsys):
    out_dir = tmp_path / "out"
    (out_dir / "reactor_optimization").mkdir(parents=True)
    _run(monkeypatch, ["init", "--template", "reactor_optimization",
                       "--output-dir", str(out_dir)])
    out = capsys.readouterr().out
    assert "already exists" in out


# ---------------------------------------------------------------------------
# _print_template_rationale direct branches  (1204, 1222-1225, 1232-1233)
# ---------------------------------------------------------------------------

def _rationale_config(tmp_path, operation, name="config.json"):
    out_dir = tmp_path / operation
    out_dir.mkdir()
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _config_dict(factors=factors, operation=operation)
    (out_dir / "config.json").write_text(json.dumps(cfg))
    return str(out_dir)


def test_rationale_goal_optimization(tmp_path, capsys):
    out_dir = _rationale_config(tmp_path, "latin_hypercube")
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    assert "Inferred goal: optimization" in out


def test_rationale_goal_else_screening(tmp_path, capsys):
    out_dir = _rationale_config(tmp_path, "full_factorial")
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    assert "Inferred goal: screening" in out


def test_rationale_zero_factors_returns(tmp_path, monkeypatch, capsys):
    out_dir = _rationale_config(tmp_path, "full_factorial")
    from doe.models import DOEConfig, RunnerConfig
    empty = DOEConfig(
        factors=[], fixed_factors={}, responses=[], block_count=1,
        test_script="", operation="full_factorial",
        processed_directory="", out_directory="results",
    )
    monkeypatch.setattr(doe.config, "load_config", lambda *a, **k: empty)
    monkeypatch.setattr(
        doe.design, "generate_design",
        lambda *a, **k: DesignMatrix(runs=[], factor_names=[],
                                     operation="full_factorial"))
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    # Bails at n_factors == 0 before printing any "Inferred goal" line.
    assert "Inferred goal" not in out


def test_rationale_import_failure(tmp_path, monkeypatch, capsys):
    out_dir = _rationale_config(tmp_path, "full_factorial")
    # `from doe.suggest import suggest` fails -> early return (1190-1191).
    monkeypatch.delattr(doe.suggest, "suggest")
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    assert "Inferred goal" not in out


def test_rationale_load_config_raises(tmp_path, monkeypatch, capsys):
    out_dir = _rationale_config(tmp_path, "full_factorial")

    def _boom(*a, **k):
        raise ValueError("bad config")

    # load_config raises inside the cfg/matrix try -> early return (1199-1200).
    monkeypatch.setattr(doe.config, "load_config", _boom)
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    assert "Inferred goal" not in out


def test_rationale_suggest_raises(tmp_path, monkeypatch, capsys):
    out_dir = _rationale_config(tmp_path, "full_factorial")

    def _boom(**kw):
        raise RuntimeError("suggest failed")

    monkeypatch.setattr(doe.suggest, "suggest", _boom)
    doe.cli._print_template_rationale(out_dir, {})
    out = capsys.readouterr().out
    assert "Inferred goal" not in out  # returned before the print block


# ---------------------------------------------------------------------------
# record: KeyboardInterrupt + existing-result + invalid-input branches
#   (1271-1272, 1291-1292, 1301-1309, 1327-1328)
# ---------------------------------------------------------------------------

def _record_setup(tmp_path):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    return cfg, out_dir, matrix


def test_record_all_keyboard_interrupt(tmp_path, monkeypatch, capsys):
    cfg, out_dir, matrix = _record_setup(tmp_path)

    def _interrupt(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", _interrupt)
    _run(monkeypatch, ["record", "--config", cfg, "--run", "all"])
    out = capsys.readouterr().out
    assert "Recording interrupted" in out


def test_record_single_keyboard_interrupt(tmp_path, monkeypatch, capsys):
    cfg, out_dir, matrix = _record_setup(tmp_path)

    def _interrupt(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", _interrupt)
    _run(monkeypatch, ["record", "--config", cfg, "--run", "1"])
    out = capsys.readouterr().out
    assert "Recording cancelled" in out


def test_record_single_existing_skip(tmp_path, monkeypatch, capsys):
    cfg, out_dir, matrix = _record_setup(tmp_path)
    rid = matrix.runs[0].run_id
    _write_results(out_dir, {rid: {"response": 3.14}})
    monkeypatch.setattr("builtins.input", lambda *a, **k: "n")
    _run(monkeypatch, ["record", "--config", cfg, "--run", str(rid)])
    out = capsys.readouterr().out
    assert "already has recorded results" in out
    assert f"Skipping run {rid}" in out


def test_record_single_invalid_then_valid(tmp_path, monkeypatch, capsys):
    cfg, out_dir, matrix = _record_setup(tmp_path)
    rid = matrix.runs[0].run_id
    answers = iter(["not-a-number", "7.5"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    _run(monkeypatch, ["record", "--config", cfg, "--run", str(rid)])
    out = capsys.readouterr().out
    assert "Invalid number" in out
    assert "Saved" in out


# ---------------------------------------------------------------------------
# export-worksheet: multiple blocks + existing results + fixed factors
#   (1431, 1442-1443, 1450, 1556-1557)
# ---------------------------------------------------------------------------

def test_worksheet_multiple_blocks_with_results(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(
        out_directory=out_dir, block_count=2))
    _populate_results(cfg, out_dir)
    _run(monkeypatch, ["export-worksheet", "--config", cfg, "--format", "csv"])
    out = capsys.readouterr().out
    assert "Block" in out
    assert "Run" in out


def test_worksheet_markdown_fixed_factors(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(
        out_directory=out_dir, fixed_factors={"Z": "5"}))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["export-worksheet", "--config", cfg,
                       "--format", "markdown"])
    out = capsys.readouterr().out
    assert "Fixed: Z = 5" in out


# ---------------------------------------------------------------------------
# sensitivity branches
#   (1606-1607, 1609, 1621-1622, 1640-1642, 1648-1651, 1666, 1668)
# ---------------------------------------------------------------------------

def test_sensitivity_nonnumeric_and_equal_levels(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["x", "y"]},   # non-numeric
        {"name": "B", "type": "continuous", "levels": ["5", "5"]},   # low == high
        {"name": "C", "type": "continuous", "levels": ["1", "9"]},   # usable
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _write_results(out_dir, {
        run.run_id: {"response": 3.0 * float(run.factor_values["C"]) + run.run_id}
        for run in matrix.runs})
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir,
                       "--n-samples", "8"])
    out = capsys.readouterr().out
    assert "Sensitivity" in out


def test_sensitivity_response_not_found(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir,
                       "--response", "does_not_exist"])
    out = capsys.readouterr().out
    assert "not found in config" in out


def test_sensitivity_not_enough_observations(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
        {"name": "C", "type": "continuous", "levels": ["3", "9"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="full_factorial", out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)  # 8 runs < 11 required for quadratic k=3
    doe.cli._save_matrix(matrix, out_dir)
    _write_results(out_dir, {
        run.run_id: {"response": float(run.run_id)} for run in matrix.runs})
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir])
    out = capsys.readouterr().out
    assert "not enough observations" in out


def test_sensitivity_fit_fails(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    _write_results(out_dir, {
        run.run_id: {"response": float(run.run_id) + 1.0} for run in matrix.runs})

    def _boom(*a, **k):
        raise RuntimeError("singular matrix")

    monkeypatch.setattr(doe.rsm, "fit_rsm", _boom)
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir,
                       "--n-samples", "8"])
    out = capsys.readouterr().out
    assert "surrogate fit failed" in out


def test_sensitivity_constant_surrogate(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "5"]},
        {"name": "B", "type": "continuous", "levels": ["2", "8"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(
        factors=factors, operation="central_composite", out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    # Identical response for every run -> constant surrogate, empty indices.
    _write_results(out_dir, {
        run.run_id: {"response": 5.0} for run in matrix.runs})
    _run(monkeypatch, ["sensitivity", "--config", cfg, "--results-dir", out_dir,
                       "--n-samples", "8"])
    out = capsys.readouterr().out
    assert "essentially constant" in out


# ---------------------------------------------------------------------------
# power: achieved_power returns None  (lines 1749-1750)
# ---------------------------------------------------------------------------

def test_power_returns_none(tmp_path, monkeypatch, capsys):
    out_dir = str(tmp_path / "results")
    cfg = _write_config(tmp_path, _config_dict(out_directory=out_dir))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    doe.cli._save_matrix(matrix, out_dir)
    monkeypatch.setattr(doe.power, "achieved_power", lambda **kw: None)
    _run(monkeypatch, ["power", "--config", cfg, "--sigma", "1.0", "--delta", "2.0"])
    out = capsys.readouterr().out
    assert "Cannot compute power" in out


# ---------------------------------------------------------------------------
# _print_matrix: fixed_factors line  (1772-1773)
# ---------------------------------------------------------------------------

def test_print_matrix_fixed_factors(tmp_path, monkeypatch, capsys):
    cfg = _write_config(tmp_path, _config_dict(fixed_factors={"Z": "9"}))
    _run(monkeypatch, ["info", "--config", cfg])
    out = capsys.readouterr().out
    assert "Fixed" in out and "Z=9" in out


# ---------------------------------------------------------------------------
# compare: notes / no-data response / flipped sign / decomposition notes
#   (1836, 1841-1843, 1866, 1872)
# ---------------------------------------------------------------------------

def _save_matrix_subset(matrix, directory, drop_last=0):
    """Persist a (possibly truncated) matrix into ``directory``."""
    runs = matrix.runs[:len(matrix.runs) - drop_last] if drop_last else matrix.runs
    trimmed = DesignMatrix(runs=runs, factor_names=matrix.factor_names,
                           operation=matrix.operation, metadata=dict(matrix.metadata))
    doe.cli._save_matrix(trimmed, directory)
    return trimmed


def test_compare_notes_and_no_data_response(tmp_path, monkeypatch, capsys):
    responses = [
        {"name": "r1", "optimize": "maximize"},
        {"name": "r2", "optimize": "maximize"},
    ]
    cfg = _write_config(tmp_path, _config_dict(responses=responses))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    base = str(tmp_path / "baseline")
    cand = str(tmp_path / "candidate")
    os.makedirs(base, exist_ok=True)
    os.makedirs(cand, exist_ok=True)
    doe.cli._save_matrix(matrix, base)
    # Candidate drops one run -> only_baseline note (line 1836).
    trimmed = _save_matrix_subset(matrix, cand, drop_last=1)
    # Only r1 has values in both sessions; r2 has none -> n_matched==0 (1841-1843).
    for d, runs in ((base, matrix.runs), (cand, trimmed.runs)):
        _write_results(d, {run.run_id: {"r1": 10.0 + run.run_id * 0.5}
                           for run in runs})
    _run(monkeypatch, ["compare", "--config", cfg, "--baseline", base,
                       "--candidate", cand])
    out = capsys.readouterr().out
    assert "only in baseline" in out
    assert "No matched runs had a value for 'r2'" in out


def test_compare_flipped_sign(tmp_path, monkeypatch, capsys):
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "2"]},
        {"name": "B", "type": "continuous", "levels": ["10", "20"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(factors=factors))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    base = str(tmp_path / "baseline")
    cand = str(tmp_path / "candidate")
    for d in (base, cand):
        os.makedirs(d, exist_ok=True)
        doe.cli._save_matrix(matrix, d)
    # Baseline: A has a positive effect; candidate: A effect flips negative.
    _write_results(base, {
        run.run_id: {"response": 2.0 * float(run.factor_values["A"])
                     + 0.5 * float(run.factor_values["B"])}
        for run in matrix.runs})
    _write_results(cand, {
        run.run_id: {"response": 100.0 - 2.0 * float(run.factor_values["A"])
                     + 0.5 * float(run.factor_values["B"])}
        for run in matrix.runs})
    _run(monkeypatch, ["compare", "--config", cfg, "--baseline", base,
                       "--candidate", cand])
    out = capsys.readouterr().out
    assert "sign flipped between sessions" in out


def test_compare_decomposition_notes(tmp_path, monkeypatch, capsys):
    # A 3-level factor makes the delta decomposition bail with a note.
    factors = [
        {"name": "A", "type": "continuous", "levels": ["1", "2", "3"]},
        {"name": "B", "type": "continuous", "levels": ["10", "20"]},
    ]
    cfg = _write_config(tmp_path, _config_dict(factors=factors))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    base = str(tmp_path / "baseline")
    cand = str(tmp_path / "candidate")
    for d, bump in ((base, 0.0), (cand, 2.0)):
        os.makedirs(d, exist_ok=True)
        doe.cli._save_matrix(matrix, d)
        _write_results(d, {
            run.run_id: {"response": 10.0 + run.run_id * 0.5 + bump}
            for run in matrix.runs})
    _run(monkeypatch, ["compare", "--config", cfg, "--baseline", base,
                       "--candidate", cand])
    out = capsys.readouterr().out
    assert "Decomposition skipped" in out


# ---------------------------------------------------------------------------
# trend: report notes / no-data response / per-response notes
#   (1799, 1804-1806, 1826)
# ---------------------------------------------------------------------------

def test_trend_notes_and_no_data_response(tmp_path, monkeypatch, capsys):
    responses = [
        {"name": "r1", "optimize": "maximize"},
        {"name": "r2", "optimize": "maximize"},
    ]
    cfg = _write_config(tmp_path, _config_dict(responses=responses))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    sessions = []
    for i in range(3):
        d = str(tmp_path / f"sess{i}")
        os.makedirs(d, exist_ok=True)
        # Session 0 keeps all runs; the others drop one -> report note (1799).
        runs = matrix.runs if i == 0 else matrix.runs[:-1]
        trimmed = DesignMatrix(runs=runs, factor_names=matrix.factor_names,
                               operation=matrix.operation,
                               metadata=dict(matrix.metadata))
        doe.cli._save_matrix(trimmed, d)
        _write_results(d, {run.run_id: {"r1": 10.0 + run.run_id * 0.5 + i}
                           for run in runs})
        sessions.append(d)
    _run(monkeypatch, ["trend", "--config", cfg, "--sessions"] + sessions)
    out = capsys.readouterr().out
    assert "were skipped" in out  # report-level note
    assert "No matched runs had a value for 'r2'" in out


def test_trend_per_response_notes(tmp_path, monkeypatch, capsys):
    # Single 3-level factor -> slope-drift fit skipped with a per-response note.
    factors = [{"name": "A", "type": "continuous", "levels": ["1", "2", "3"]}]
    cfg = _write_config(tmp_path, _config_dict(factors=factors))
    cfg_obj = load_config(cfg, strict=False)
    matrix = generate_design(cfg_obj)
    sessions = []
    for i in range(3):
        d = str(tmp_path / f"s{i}")
        os.makedirs(d, exist_ok=True)
        doe.cli._save_matrix(matrix, d)
        _write_results(d, {run.run_id: {"response": 5.0 + run.run_id + i}
                           for run in matrix.runs})
        sessions.append(d)
    _run(monkeypatch, ["trend", "--config", cfg, "--sessions"] + sessions)
    out = capsys.readouterr().out
    assert "slope-drift fit skipped" in out


# ---------------------------------------------------------------------------
# _print_report / _print_alias_structure: rich formatting branches
#   (1917, 1926, 1972, 1984, 2004-2010, 2029, 2049-2050, 2057-2070, 2093, 2095)
# ---------------------------------------------------------------------------

def _summary_stats():
    return {"A": {"low": {"n": 2, "mean": 1.0, "std": 0.1, "min": 0.5, "max": 1.5}}}


def test_print_report_full(capsys):
    resp1 = ResponseAnalysis(
        response_name="r1",
        effects=[EffectResult("A", 1.5, 0.2, 40.0)],
        summary_stats=_summary_stats(),
        interactions=[InteractionEffect("A", "B", 0.3, 5.0)],
        anova_table=AnovaTable(
            rows=[AnovaRow("A", 1, 10.0, 10.0, 5.0, 0.03)],
            lack_of_fit_row=AnovaRow("Lack of Fit", 2, 4.0, 2.0, 3.0, 0.01),
            pure_error_row=AnovaRow("Pure Error", 3, 3.0, 1.0),
            error_row=AnovaRow("Error", 5, 7.0, 1.4),
            total_row=AnovaRow("Total", 6, 17.0, 2.8),
            error_method="replicates",
        ),
        ordinal_trends=[OrdinalTrendResult(
            factor_name="A", response_name="r1",
            linear_coefficient=0.5, linear_ss=2.0,
            linear_f_value=4.0, linear_p_value=0.02,
            quadratic_coefficient=0.1, r_squared_quadratic=0.9)],
        model_adequacy=ModelAdequacy(
            model_type="quadratic", n_observations=8, n_parameters=4,
            r_squared=0.9, adj_r_squared=0.85, predicted_r_squared=0.8,
            press=1.0, shapiro_w=0.95, shapiro_p=0.2, durbin_watson=2.0,
            runorder_drift_slope=0.01, runorder_drift_p=0.5,
            max_leverage=0.6, leverage_threshold=0.5,
            high_leverage_run_ids=[3], max_cooks_distance=0.4,
            cooks_threshold=0.5, high_influence_run_ids=[2], notes=["adq note"]),
        stationary_point=StationaryPoint(
            nature="ridge", coded_location={"A": 0.1, "B": 0.0},
            natural_location={"A": "1.1", "B": "15"}, predicted_value=5.0,
            eigenvalues=[0.0, -1.0], eigenvectors=[[1.0, 0.0], [0.0, 1.0]],
            factor_order=["A", "B"], inside_design_region=True,
            ridge_direction={"A": 0.7, "B": 0.7}),
        scheffe_model=ScheffeModel(
            response_name="r1", model_form="quadratic",
            component_names=["A", "B"], n_observations=8, n_parameters=3,
            r_squared=0.9, adj_r_squared=0.85, residual_ms=0.5,
            terms=[ScheffeTerm("A", 1.0, 0.1, 10.0, 0.001),
                   ScheffeTerm("A*B", 0.5, None, None, None)],
            notes=["scheffe note"]),
    )
    resp2 = ResponseAnalysis(
        response_name="r2",
        effects=[EffectResult("A", 1.0, 0.1, 50.0)],
        summary_stats=_summary_stats(),
        anova_table=AnovaTable(
            rows=[AnovaRow("A", 1, 5.0, 5.0, 2.0, 0.1)],
            error_method="split_plot"),
    )
    report = AnalysisReport(
        results_by_response={"r1": resp1, "r2": resp2},
        pareto_chart_paths={"r1": "pareto_r1.png"},
        effects_plot_paths={"r1": "effects_r1.png"},
        alias_structure=AliasStructure(
            design_type="fractional_factorial", resolution=3,
            notes=["alias note"],
            main_effects=[AliasEntry("A", [("BC", 1.0)]), AliasEntry("D", [])],
            two_factor_interactions=[]),
    )
    doe.cli._print_report(report)
    out = capsys.readouterr().out
    assert "Alias Structure" in out
    assert "Ordinal Trends" in out
    assert "high-leverage runs" in out
    assert "Ridge axis" in out
    assert "Scheffé Canonical" in out
    assert "split-plot ANOVA" in out
    assert "Lack-of-fit p=0.0100" in out
    assert "Pareto chart (r1): pareto_r1.png" in out
    assert "Main effects (r1): effects_r1.png" in out
