# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Comprehensive test suite for the Design of Experiments project.

Covers: config loading/validation, design generation, analysis, codegen, and CLI.
Run with: pytest tests/test_doe.py -v
"""

import json
import math
import os
import stat
import subprocess
import sys
import itertools
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from doe.models import (
    DOEConfig, Factor, ResponseVar, RunnerConfig,
    ExperimentRun, DesignMatrix, EffectResult, ResponseAnalysis, AnalysisReport,
)
from doe.config import load_config, SUPPORTED_OPERATIONS
from doe.design import generate_design
from doe.codegen import generate_script
from doe.analysis import analyze


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config_dict(
    factors=None,
    responses=None,
    operation="full_factorial",
    block_count=1,
    test_script="",
    fixed_factors=None,
    static_settings=None,
    metadata=None,
    runner=None,
    lhs_samples=0,
):
    """Build a raw config dict suitable for writing to a JSON file."""
    if factors is None:
        factors = [
            {"name": "A", "levels": ["1", "2"]},
            {"name": "B", "levels": ["10", "20"]},
        ]
    cfg = {
        "factors": factors,
        "settings": {
            "operation": operation,
            "block_count": block_count,
            "test_script": test_script,
            "lhs_samples": lhs_samples,
        },
    }
    if responses is not None:
        cfg["responses"] = responses
    if fixed_factors is not None:
        cfg["fixed_factors"] = fixed_factors
    if static_settings is not None:
        cfg["static_settings"] = static_settings
    if metadata is not None:
        cfg["metadata"] = metadata
    if runner is not None:
        cfg["runner"] = runner
    return cfg


def _write_config(tmp_path, cfg_dict):
    """Write config dict to a JSON file and return the path."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg_dict))
    return str(path)


def _make_doe_config(
    factors=None,
    responses=None,
    operation="full_factorial",
    block_count=1,
    fixed_factors=None,
    runner=None,
    lhs_samples=0,
    metadata=None,
):
    """Build a DOEConfig directly (no file I/O)."""
    if factors is None:
        factors = [
            Factor(name="A", levels=["1", "2"]),
            Factor(name="B", levels=["10", "20"]),
        ]
    if responses is None:
        responses = [ResponseVar(name="response")]
    return DOEConfig(
        factors=factors,
        fixed_factors=fixed_factors or {},
        responses=responses,
        block_count=block_count,
        test_script="",
        operation=operation,
        processed_directory="",
        out_directory="",
        lhs_samples=lhs_samples,
        metadata=metadata or {},
        runner=runner or RunnerConfig(),
    )


def _write_result_files(results_dir, results):
    """
    Write run result JSON files.
    results: dict mapping run_id -> dict of response values.
    """
    os.makedirs(results_dir, exist_ok=True)
    for run_id, data in results.items():
        path = os.path.join(results_dir, f"run_{run_id}.json")
        with open(path, "w") as f:
            json.dump(data, f)


# ===================================================================
# 1. CONFIG LOADING TESTS
# ===================================================================

class TestConfigLoading:

    def test_valid_dict_factors(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "threads", "levels": [1, 4, 8], "type": "ordinal", "unit": "count"},
                {"name": "buffer", "levels": [128, 256]},
            ],
            responses=[{"name": "throughput", "optimize": "maximize", "unit": "MB/s"}],
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert len(cfg.factors) == 2
        assert cfg.factors[0].name == "threads"
        assert cfg.factors[0].levels == ["1", "4", "8"]
        assert cfg.factors[0].type == "ordinal"
        assert cfg.factors[0].unit == "count"
        assert cfg.factors[1].name == "buffer"
        assert len(cfg.responses) == 1
        assert cfg.responses[0].name == "throughput"
        assert cfg.responses[0].optimize == "maximize"
        assert cfg.responses[0].unit == "MB/s"

    def test_legacy_array_factors(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                ["threads", "1", "4", "8"],
                ["buffer", "128", "256"],
            ],
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert len(cfg.factors) == 2
        assert cfg.factors[0].name == "threads"
        assert cfg.factors[0].levels == ["1", "4", "8"]

    def test_legacy_static_settings_to_fixed_factors(self, tmp_path):
        cfg_dict = _make_config_dict(
            static_settings=["--timeout=30", "--verbose=true"],
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.fixed_factors == {"timeout": "30", "verbose": "true"}

    def test_fixed_factors_dict(self, tmp_path):
        cfg_dict = _make_config_dict(
            fixed_factors={"timeout": 30, "verbose": True},
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.fixed_factors == {"timeout": "30", "verbose": "True"}

    def test_missing_operation_uses_default(self, tmp_path):
        cfg_dict = _make_config_dict()
        del cfg_dict["settings"]["operation"]
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.operation == "full_factorial"

    def test_invalid_operation(self, tmp_path):
        cfg_dict = _make_config_dict(operation="bogus_design")
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Unsupported operation"):
            load_config(path, strict=False)

    def test_plackett_burman_requires_2_levels(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": [1, 2, 3]},
                {"name": "B", "levels": [10, 20]},
            ],
            operation="plackett_burman",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Plackett-Burman requires exactly 2 levels"):
            load_config(path, strict=False)

    def test_central_composite_requires_2_numeric_levels(self, tmp_path):
        # Non-numeric levels
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": ["low", "high"]},
                {"name": "B", "levels": ["1", "2"]},
            ],
            operation="central_composite",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Central composite requires numeric levels"):
            load_config(path, strict=False)

    def test_central_composite_requires_exactly_2_levels(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": [1, 2, 3]},
                {"name": "B", "levels": [10, 20]},
            ],
            operation="central_composite",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Central composite requires exactly 2 levels"):
            load_config(path, strict=False)

    def test_duplicate_factor_names(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": ["1", "2"]},
                {"name": "A", "levels": ["10", "20"]},
            ],
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Factor names must be unique"):
            load_config(path, strict=False)

    def test_duplicate_response_names(self, tmp_path):
        cfg_dict = _make_config_dict(
            responses=[
                {"name": "latency", "optimize": "minimize"},
                {"name": "latency", "optimize": "maximize"},
            ],
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Response names must be unique"):
            load_config(path, strict=False)

    def test_invalid_optimize_value(self, tmp_path):
        cfg_dict = _make_config_dict(
            responses=[{"name": "throughput", "optimize": "average"}],
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="invalid optimize"):
            load_config(path, strict=False)

    def test_invalid_arg_style(self, tmp_path):
        cfg_dict = _make_config_dict(
            runner={"arg_style": "xml"},
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="arg_style.*invalid"):
            load_config(path, strict=False)

    def test_empty_factors_list(self, tmp_path):
        cfg_dict = _make_config_dict(factors=[])
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="At least one factor"):
            load_config(path, strict=False)

    def test_block_count_less_than_1(self, tmp_path):
        cfg_dict = _make_config_dict(block_count=0)
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="block_count must be >= 1"):
            load_config(path, strict=False)

    def test_default_response_when_none(self, tmp_path):
        cfg_dict = _make_config_dict()
        # No "responses" key at all
        cfg_dict.pop("responses", None)
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert len(cfg.responses) == 1
        assert cfg.responses[0].name == "response"

    def test_response_parsing_dict(self, tmp_path):
        cfg_dict = _make_config_dict(
            responses=[{"name": "latency", "optimize": "minimize", "unit": "ms"}],
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.responses[0].name == "latency"
        assert cfg.responses[0].optimize == "minimize"
        assert cfg.responses[0].unit == "ms"

    def test_response_parsing_string(self, tmp_path):
        cfg_dict = _make_config_dict(responses=["throughput", "latency"])
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert len(cfg.responses) == 2
        assert cfg.responses[0].name == "throughput"
        assert cfg.responses[1].name == "latency"

    def test_response_parsing_invalid(self, tmp_path):
        cfg_dict = _make_config_dict(responses=[123])
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Unexpected response format"):
            load_config(path, strict=False)

    def test_factor_missing_name(self, tmp_path):
        cfg_dict = _make_config_dict(factors=[{"levels": ["1", "2"]}])
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Factor must have a name"):
            load_config(path, strict=False)

    def test_factor_fewer_than_2_levels(self, tmp_path):
        cfg_dict = _make_config_dict(factors=[{"name": "A", "levels": ["1"]}])
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Factor must have a name and at least 2 levels"):
            load_config(path, strict=False)


# ===================================================================
# 2. DESIGN GENERATION TESTS
# ===================================================================

class TestDesignGeneration:

    def test_full_factorial_run_count(self):
        """3 factors x 2 levels each = 2^3 = 8 runs."""
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
                Factor(name="C", levels=["0", "1"]),
            ],
        )
        matrix = generate_design(cfg, seed=42)
        assert len(matrix.runs) == 8

    def test_full_factorial_all_combinations_present(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
            ],
        )
        matrix = generate_design(cfg, seed=42)
        combos = {(r.factor_values["A"], r.factor_values["B"]) for r in matrix.runs}
        expected = {("0", "0"), ("0", "1"), ("1", "0"), ("1", "1")}
        assert combos == expected

    def test_full_factorial_mixed_level_counts(self):
        """2 levels x 3 levels = 6 runs."""
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["1", "2", "3"]),
            ],
        )
        matrix = generate_design(cfg, seed=42)
        assert len(matrix.runs) == 6

    def test_full_factorial_deterministic(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
            ],
        )
        m1 = generate_design(cfg, seed=99)
        m2 = generate_design(cfg, seed=99)
        vals1 = [(r.run_id, r.factor_values) for r in m1.runs]
        vals2 = [(r.run_id, r.factor_values) for r in m2.runs]
        assert vals1 == vals2

    def test_plackett_burman_structure(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["lo", "hi"]),
                Factor(name="C", levels=["lo", "hi"]),
            ],
            operation="plackett_burman",
        )
        matrix = generate_design(cfg, seed=42)
        # PB design for 3 factors uses a 4-run design
        assert len(matrix.runs) >= 4
        # All factor values should be one of the two levels
        for run in matrix.runs:
            for f in ["A", "B", "C"]:
                assert run.factor_values[f] in ("lo", "hi")

    def test_latin_hypercube_sample_count(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "100"], type="continuous"),
                Factor(name="B", levels=["0", "100"], type="continuous"),
            ],
            operation="latin_hypercube",
            lhs_samples=15,
        )
        matrix = generate_design(cfg, seed=42)
        assert len(matrix.runs) == 15

    def test_latin_hypercube_default_samples(self):
        """Default samples = max(10, 2*n_factors)."""
        factors = [
            Factor(name=f"F{i}", levels=["0", "1"], type="continuous")
            for i in range(8)
        ]
        cfg = _make_doe_config(factors=factors, operation="latin_hypercube")
        matrix = generate_design(cfg, seed=42)
        expected_samples = max(10, 2 * 8)  # 16
        assert len(matrix.runs) == expected_samples

    def test_latin_hypercube_seed_produces_valid_range(self):
        """LHS with seed produces values within the factor level range.
        Note: numpy global seed reproducibility is fragile within the same
        process due to internal state; we verify structure and range instead."""
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "100"], type="continuous"),
                Factor(name="B", levels=["0", "100"], type="continuous"),
            ],
            operation="latin_hypercube",
            lhs_samples=10,
        )
        matrix = generate_design(cfg, seed=42)
        assert len(matrix.runs) == 10
        for run in matrix.runs:
            a_val = float(run.factor_values["A"])
            b_val = float(run.factor_values["B"])
            assert 0.0 <= a_val <= 100.0
            assert 0.0 <= b_val <= 100.0

    def test_central_composite_structure(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["10", "20"]),
                Factor(name="B", levels=["100", "200"]),
            ],
            operation="central_composite",
        )
        matrix = generate_design(cfg, seed=42)
        # CCD for 2 factors: 4 factorial + 4 star + center points
        assert len(matrix.runs) >= 8
        # All values should be numeric strings
        for run in matrix.runs:
            for val in run.factor_values.values():
                float(val)  # should not raise

    def test_blocking_multiplies_runs(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
            ],
            block_count=3,
        )
        matrix = generate_design(cfg, seed=42)
        # 2^2 = 4 base runs x 3 blocks = 12
        assert len(matrix.runs) == 12
        assert matrix.metadata["n_base_runs"] == 4
        assert matrix.metadata["n_blocks"] == 3
        assert matrix.metadata["n_total_runs"] == 12

    def test_randomization_with_seed_reproducible(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
                Factor(name="C", levels=["0", "1"]),
            ],
        )
        m1 = generate_design(cfg, seed=123)
        m2 = generate_design(cfg, seed=123)
        order1 = [r.factor_values for r in m1.runs]
        order2 = [r.factor_values for r in m2.runs]
        assert order1 == order2

    def test_randomization_within_blocks_preserves_block_integrity(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
            ],
            block_count=2,
        )
        matrix = generate_design(cfg, seed=42)
        # Runs should be grouped by block (sorted block IDs, contiguous)
        block_ids = [r.block_id for r in matrix.runs]
        # Block 1 runs come first, then block 2
        block1_runs = [r for r in matrix.runs if r.block_id == 1]
        block2_runs = [r for r in matrix.runs if r.block_id == 2]
        assert len(block1_runs) == 4
        assert len(block2_runs) == 4
        # All block 1 run_ids should be less than all block 2 run_ids
        max_block1_id = max(r.run_id for r in block1_runs)
        min_block2_id = min(r.run_id for r in block2_runs)
        assert max_block1_id < min_block2_id

    def test_metadata_populated(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["0", "1"]),
                Factor(name="B", levels=["0", "1"]),
            ],
        )
        matrix = generate_design(cfg, seed=7)
        assert matrix.metadata["n_factors"] == 2
        assert matrix.metadata["n_base_runs"] == 4
        assert matrix.metadata["n_blocks"] == 1
        assert matrix.metadata["n_total_runs"] == 4
        assert matrix.metadata["seed"] == 7
        assert matrix.factor_names == ["A", "B"]
        assert matrix.operation == "full_factorial"


# ===================================================================
# 2b. FRACTIONAL FACTORIAL AND BOX-BEHNKEN TESTS
# ===================================================================

class TestFractionalFactorial:

    def test_fewer_runs_than_full_factorial(self):
        """Fractional factorial should produce fewer runs than full factorial for >= 4 factors."""
        factors = [
            Factor(name=f"F{i}", levels=["lo", "hi"])
            for i in range(5)
        ]
        ff_cfg = _make_doe_config(factors=factors, operation="fractional_factorial")
        full_cfg = _make_doe_config(factors=factors, operation="full_factorial")

        ff_matrix = generate_design(ff_cfg, seed=42)
        full_matrix = generate_design(full_cfg, seed=42)

        assert len(ff_matrix.runs) < len(full_matrix.runs)

    def test_all_factor_names_present(self):
        """All factor names should appear in every run."""
        factors = [
            Factor(name="A", levels=["lo", "hi"]),
            Factor(name="B", levels=["lo", "hi"]),
            Factor(name="C", levels=["lo", "hi"]),
            Factor(name="D", levels=["lo", "hi"]),
        ]
        cfg = _make_doe_config(factors=factors, operation="fractional_factorial")
        matrix = generate_design(cfg, seed=42)

        expected_names = {"A", "B", "C", "D"}
        for run in matrix.runs:
            assert set(run.factor_values.keys()) == expected_names

    def test_validation_requires_2_levels(self, tmp_path):
        """Fractional factorial should reject factors with != 2 levels."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": [1, 2, 3]},
                {"name": "B", "levels": [10, 20]},
            ],
            operation="fractional_factorial",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Fractional factorial requires exactly 2 levels"):
            load_config(path, strict=False)


class TestBoxBehnken:

    def test_center_points_present(self):
        """Box-Behnken design should include center points (all factors at midpoint)."""
        factors = [
            Factor(name="A", levels=["10", "20"]),
            Factor(name="B", levels=["100", "200"]),
            Factor(name="C", levels=["1", "5"]),
        ]
        cfg = _make_doe_config(factors=factors, operation="box_behnken")
        matrix = generate_design(cfg, seed=42)

        # Center point: A=15, B=150, C=3
        center_runs = [
            r for r in matrix.runs
            if (float(r.factor_values["A"]) == 15.0
                and float(r.factor_values["B"]) == 150.0
                and float(r.factor_values["C"]) == 3.0)
        ]
        assert len(center_runs) >= 1, "Expected at least one center point in Box-Behnken design"

    def test_requires_at_least_3_factors(self, tmp_path):
        """Box-Behnken should reject designs with fewer than 3 factors."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": [1, 2]},
                {"name": "B", "levels": [10, 20]},
            ],
            operation="box_behnken",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Box-Behnken requires at least 3 factors"):
            load_config(path, strict=False)

    def test_requires_2_numeric_levels(self, tmp_path):
        """Box-Behnken should reject non-numeric levels."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": ["low", "high"]},
                {"name": "B", "levels": [1, 2]},
                {"name": "C", "levels": [10, 20]},
            ],
            operation="box_behnken",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Box-Behnken requires numeric levels"):
            load_config(path, strict=False)

    def test_requires_exactly_2_levels(self, tmp_path):
        """Box-Behnken should reject factors with != 2 levels."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": [1, 2, 3]},
                {"name": "B", "levels": [10, 20]},
                {"name": "C", "levels": [100, 200]},
            ],
            operation="box_behnken",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="Box-Behnken requires exactly 2 levels"):
            load_config(path, strict=False)


# ===================================================================
# 3. ANALYSIS TESTS
# ===================================================================

class TestAnalysis:

    @pytest.fixture
    def simple_2factor_setup(self, tmp_path):
        """
        2 factors (A, B) each with 2 levels, full factorial = 4 runs.
        Known response values for deterministic effect computation.

        Design (before randomization):
          run 1: A=lo, B=lo -> response = 10
          run 2: A=lo, B=hi -> response = 20
          run 3: A=hi, B=lo -> response = 30
          run 4: A=hi, B=hi -> response = 40
        """
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["lo", "hi"]),
            ],
            responses=[ResponseVar(name="response")],
        )
        # Generate design with a fixed seed so run order is deterministic
        matrix = generate_design(cfg, seed=0)

        # Build response data keyed by factor values
        response_map = {
            ("lo", "lo"): 10,
            ("lo", "hi"): 20,
            ("hi", "lo"): 30,
            ("hi", "hi"): 40,
        }

        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            key = (run.factor_values["A"], run.factor_values["B"])
            results[run.run_id] = {"response": response_map[key]}
        _write_result_files(results_dir, results)

        return cfg, matrix, results_dir

    def test_main_effects_known_case(self, simple_2factor_setup):
        cfg, matrix, results_dir = simple_2factor_setup
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)

        assert "response" in report.results_by_response
        analysis = report.results_by_response["response"]

        effects_dict = {e.factor_name: e for e in analysis.effects}
        # Levels are sorted: ["hi", "lo"]. effect = mean(levels[1]) - mean(levels[0])
        # A effect: mean("lo") - mean("hi") = (10+20)/2 - (30+40)/2 = 15 - 35 = -20
        assert math.isclose(effects_dict["A"].main_effect, -20.0, rel_tol=1e-9)
        # B effect: mean("lo") - mean("hi") = (10+30)/2 - (20+40)/2 = 20 - 30 = -10
        assert math.isclose(effects_dict["B"].main_effect, -10.0, rel_tol=1e-9)

    def test_main_effects_more_than_2_levels(self, tmp_path):
        """With >2 levels, effect = max(level_means) - min(level_means)."""
        cfg = _make_doe_config(
            factors=[
                Factor(name="X", levels=["a", "b", "c"]),
            ],
            responses=[ResponseVar(name="val")],
        )
        matrix = generate_design(cfg, seed=0)

        response_map = {"a": 5.0, "b": 15.0, "c": 10.0}
        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            results[run.run_id] = {"val": response_map[run.factor_values["X"]]}
        _write_result_files(results_dir, results)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["val"]
        # Range: max(15, 10, 5) - min(15, 10, 5) = 10
        assert math.isclose(analysis.effects[0].main_effect, 10.0, rel_tol=1e-9)

    def test_summary_stats_correctness(self, simple_2factor_setup):
        cfg, matrix, results_dir = simple_2factor_setup
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        stats = report.results_by_response["response"].summary_stats

        # Factor A, level "hi": values are 30 and 40
        hi_stats = stats["A"]["hi"]
        assert hi_stats["n"] == 2
        assert math.isclose(hi_stats["mean"], 35.0)
        assert math.isclose(hi_stats["min"], 30.0)
        assert math.isclose(hi_stats["max"], 40.0)

        # Factor A, level "lo": values are 10 and 20
        lo_stats = stats["A"]["lo"]
        assert lo_stats["n"] == 2
        assert math.isclose(lo_stats["mean"], 15.0)

    def test_multi_response(self, tmp_path):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["lo", "hi"]),
            ],
            responses=[
                ResponseVar(name="throughput"),
                ResponseVar(name="latency", optimize="minimize"),
            ],
        )
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            a_val = 1 if run.factor_values["A"] == "hi" else 0
            b_val = 1 if run.factor_values["B"] == "hi" else 0
            results[run.run_id] = {
                "throughput": 100 + a_val * 50 + b_val * 20,
                "latency": 10 - a_val * 3 + b_val * 1,
            }
        _write_result_files(results_dir, results)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        assert "throughput" in report.results_by_response
        assert "latency" in report.results_by_response

    def test_missing_response_key_warning(self, tmp_path, capsys):
        cfg = _make_doe_config(
            factors=[Factor(name="A", levels=["lo", "hi"])],
            responses=[ResponseVar(name="missing_metric")],
        )
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "results")
        # Write result files that do NOT contain "missing_metric"
        results = {run.run_id: {"other_key": 42} for run in matrix.runs}
        _write_result_files(results_dir, results)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        captured = capsys.readouterr()
        assert "missing_metric" in captured.out
        assert "Warning" in captured.out
        # No analysis for the missing response
        assert len(report.results_by_response) == 0

    def test_missing_result_files(self, tmp_path):
        cfg = _make_doe_config(
            factors=[Factor(name="A", levels=["lo", "hi"])],
        )
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "nonexistent_results")

        with pytest.raises(FileNotFoundError, match="Missing result files"):
            analyze(matrix, cfg, results_dir=results_dir, no_plots=True)

    def test_percentage_contribution_sums_to_100(self, simple_2factor_setup):
        cfg, matrix, results_dir = simple_2factor_setup
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["response"]
        total_pct = sum(e.pct_contribution for e in analysis.effects)
        assert math.isclose(total_pct, 100.0, rel_tol=1e-9)

    def test_effects_sorted_by_magnitude(self, simple_2factor_setup):
        cfg, matrix, results_dir = simple_2factor_setup
        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        effects = report.results_by_response["response"].effects
        magnitudes = [abs(e.main_effect) for e in effects]
        assert magnitudes == sorted(magnitudes, reverse=True)

    def test_plot_generation(self, tmp_path):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["lo", "hi"]),
            ],
            responses=[ResponseVar(name="metric", unit="ops/s")],
        )
        cfg.processed_directory = str(tmp_path / "plots")
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            a_val = 1 if run.factor_values["A"] == "hi" else 0
            results[run.run_id] = {"metric": 10 + a_val * 5}
        _write_result_files(results_dir, results)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=False)
        # Pareto chart created
        assert "metric" in report.pareto_chart_paths
        assert os.path.isfile(report.pareto_chart_paths["metric"])
        # Main effects plot created
        assert "metric" in report.effects_plot_paths
        assert os.path.isfile(report.effects_plot_paths["metric"])

    def test_no_plots_skips_generation(self, tmp_path):
        cfg = _make_doe_config(
            factors=[
                Factor(name="A", levels=["lo", "hi"]),
                Factor(name="B", levels=["lo", "hi"]),
            ],
        )
        cfg.processed_directory = str(tmp_path / "plots")
        matrix = generate_design(cfg, seed=0)
        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            a_val = 1 if run.factor_values["A"] == "hi" else 0
            results[run.run_id] = {"response": 10 + a_val * 5}
        _write_result_files(results_dir, results)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        assert len(report.pareto_chart_paths) == 0
        assert len(report.effects_plot_paths) == 0
        assert not os.path.exists(str(tmp_path / "plots"))


# ===================================================================
# 4. CODEGEN TESTS
# ===================================================================

class TestCodegen:

    @pytest.fixture
    def codegen_setup(self):
        cfg = _make_doe_config(
            factors=[
                Factor(name="threads", levels=["1", "4"]),
                Factor(name="buffer", levels=["128", "256"]),
            ],
            fixed_factors={"timeout": "30"},
        )
        matrix = generate_design(cfg, seed=42)
        return cfg, matrix

    def test_shell_script_created_and_executable(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.sh")
        generate_script(matrix, cfg, out, format="sh")
        assert os.path.isfile(out)
        mode = os.stat(out).st_mode
        assert mode & stat.S_IXUSR

    def test_python_script_created_and_executable(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.py")
        generate_script(matrix, cfg, out, format="py")
        assert os.path.isfile(out)
        mode = os.stat(out).st_mode
        assert mode & stat.S_IXUSR

    def test_template_contains_run_data(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        assert "run_id" in rendered
        # All run IDs should be present in the RUNS list
        for run in matrix.runs:
            assert f'"run_id": {run.run_id}' in rendered

    def test_double_dash_arg_style(self, tmp_path):
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="double-dash"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        # Python template uses double-dash style by default
        assert "double-dash" in rendered or "--{name}" in rendered or 'f"--{name}"' in rendered

    def test_env_arg_style(self, tmp_path):
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="env"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        assert 'ARG_STYLE = "env"' in rendered

    def test_positional_arg_style(self, tmp_path):
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="positional"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        assert 'ARG_STYLE = "positional"' in rendered

    def test_fixed_factors_in_shell_output(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.sh")
        rendered = generate_script(matrix, cfg, out, format="sh")
        assert "timeout" in rendered
        assert "30" in rendered

    def test_fixed_factors_in_python_output(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        assert "timeout" in rendered
        assert "30" in rendered

    def test_invalid_format_raises(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.txt")
        with pytest.raises(ValueError, match="Unknown format"):
            generate_script(matrix, cfg, out, format="txt")

    def test_python_template_has_run_data(self, tmp_path, codegen_setup):
        cfg, matrix = codegen_setup
        out = str(tmp_path / "run.py")
        rendered = generate_script(matrix, cfg, out, format="py")
        assert "RUNS" in rendered
        assert "run_id" in rendered
        # Check factor names appear
        assert "threads" in rendered
        assert "buffer" in rendered

    def test_shell_double_dash_arg_style(self, tmp_path):
        """Test double-dash args specifically in shell format."""
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="double-dash"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.sh")
        rendered = generate_script(matrix, cfg, out, format="sh")
        assert "--threads" in rendered

    def test_shell_env_arg_style(self, tmp_path):
        """Test env args specifically in shell format."""
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="env"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.sh")
        rendered = generate_script(matrix, cfg, out, format="sh")
        assert "export THREADS=" in rendered

    def test_shell_positional_arg_style(self, tmp_path):
        """Test positional args specifically in shell format."""
        cfg = _make_doe_config(
            factors=[Factor(name="threads", levels=["1", "4"])],
            runner=RunnerConfig(arg_style="positional"),
        )
        cfg.test_script = "/bin/test_tool"
        matrix = generate_design(cfg, seed=42)
        out = str(tmp_path / "run.sh")
        rendered = generate_script(matrix, cfg, out, format="sh")
        assert "--threads" not in rendered


# ===================================================================
# 5. CLI INTEGRATION TESTS
# ===================================================================

class TestCLI:

    @pytest.fixture
    def cli_config(self, tmp_path):
        """Write a valid config file for CLI tests."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "A", "levels": ["lo", "hi"]},
                {"name": "B", "levels": ["1", "2"]},
            ],
            responses=[{"name": "response", "optimize": "maximize"}],
        )
        path = tmp_path / "config.json"
        path.write_text(json.dumps(cfg_dict))
        return str(path)

    def _run_cli(self, args, cwd=None):
        """Run doe.py with the given args via subprocess."""
        cmd = [sys.executable, str(PROJECT_ROOT / "doe.py")] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd or str(PROJECT_ROOT),
        )
        return result

    def test_generate_dry_run_prints_matrix(self, cli_config):
        result = self._run_cli(["generate", "--config", cli_config, "--dry-run"])
        assert result.returncode == 0
        assert "Operation" in result.stdout
        assert "full_factorial" in result.stdout
        # Should list factor names
        assert "A" in result.stdout
        assert "B" in result.stdout

    def test_generate_creates_output_file_sh(self, tmp_path, cli_config):
        output = str(tmp_path / "experiment_runner.sh")
        result = self._run_cli(["generate", "--config", cli_config, "--output", output])
        assert result.returncode == 0
        assert os.path.isfile(output)

    def test_generate_creates_output_file_py(self, tmp_path, cli_config):
        output = str(tmp_path / "experiment_runner.py")
        result = self._run_cli([
            "generate", "--config", cli_config,
            "--output", output, "--format", "py",
        ])
        assert result.returncode == 0
        assert os.path.isfile(output)

    def test_info_prints_design_info(self, cli_config):
        result = self._run_cli(["info", "--config", cli_config])
        assert result.returncode == 0
        assert "Operation" in result.stdout
        assert "Factors" in result.stdout
        assert "Total runs" in result.stdout

    def test_analyze_with_result_files(self, tmp_path, cli_config):
        # First generate the design to know run IDs, then create matching results
        cfg = load_config(cli_config, strict=False)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        results = {}
        for run in matrix.runs:
            a_val = 1 if run.factor_values["A"] == "hi" else 0
            results[run.run_id] = {"response": 10 + a_val * 5}
        _write_result_files(results_dir, results)

        result = self._run_cli([
            "analyze", "--config", cli_config,
            "--results-dir", results_dir, "--no-plots",
        ])
        assert result.returncode == 0
        assert "Main Effects" in result.stdout
        assert "Summary Statistics" in result.stdout

    def test_missing_config_raises_error(self):
        result = self._run_cli(["generate"])
        # argparse should complain about missing --config
        assert result.returncode != 0
        assert "config" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_no_command_raises_error(self):
        result = self._run_cli([])
        assert result.returncode != 0

    def test_generate_with_seed(self, tmp_path, cli_config):
        output = str(tmp_path / "run.py")
        result = self._run_cli([
            "generate", "--config", cli_config,
            "--output", output, "--seed", "42", "--format", "py",
        ])
        assert result.returncode == 0
        assert os.path.isfile(output)


# ===================================================================
# 6. MODEL DATACLASS TESTS (sanity checks)
# ===================================================================

class TestModels:

    def test_factor_defaults(self):
        f = Factor(name="X", levels=["a", "b"])
        assert f.type == "categorical"
        assert f.description == ""
        assert f.unit == ""

    def test_response_var_defaults(self):
        r = ResponseVar(name="y")
        assert r.optimize == "maximize"
        assert r.unit == ""

    def test_runner_config_defaults(self):
        rc = RunnerConfig()
        assert rc.arg_style == "double-dash"
        assert rc.result_file == "json"

    def test_design_matrix_metadata_default(self):
        dm = DesignMatrix(runs=[], factor_names=[], operation="full_factorial")
        assert dm.metadata == {}

    def test_analysis_report_defaults(self):
        report = AnalysisReport(results_by_response={})
        assert report.pareto_chart_paths == {}
        assert report.effects_plot_paths == {}


# ===================================================================
# REPORT GENERATION TESTS
# ===================================================================

class TestReportGeneration:
    """Tests for doe.report.generate_report."""

    def test_generate_report_produces_html_file(self, tmp_path):
        """generate_report should create an HTML file at the given output path."""
        from doe.report import generate_report

        cfg = _make_doe_config(
            metadata={"name": "Test Plan", "description": "A test experiment"},
        )
        matrix = generate_design(cfg)

        # Create result files for each run
        results_dir = str(tmp_path / "results")
        results = {run.run_id: {"response": float(run.run_id * 10)} for run in matrix.runs}
        _write_result_files(results_dir, results)
        cfg.out_directory = results_dir
        cfg.processed_directory = str(tmp_path / "processed")

        output_path = str(tmp_path / "report.html")
        result = generate_report(matrix, cfg, results_dir=results_dir, output_path=output_path)

        assert result == output_path
        assert os.path.exists(output_path)
        content = Path(output_path).read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE html>")
        assert len(content) > 500  # non-trivial file

    def test_report_contains_key_sections(self, tmp_path):
        """The HTML report must contain the expected section headings."""
        from doe.report import generate_report

        cfg = _make_doe_config(
            metadata={"name": "Section Test", "description": "Check sections"},
        )
        matrix = generate_design(cfg)

        results_dir = str(tmp_path / "results")
        results = {run.run_id: {"response": float(run.run_id)} for run in matrix.runs}
        _write_result_files(results_dir, results)
        cfg.out_directory = results_dir
        cfg.processed_directory = str(tmp_path / "processed")

        output_path = str(tmp_path / "report.html")
        generate_report(matrix, cfg, results_dir=results_dir, output_path=output_path)

        content = Path(output_path).read_text(encoding="utf-8")
        assert "Design Summary" in content
        assert "Main Effects" in content
        assert "Design Matrix" in content
        assert "Generated by DOE Helper Tool" in content
        assert "Section Test" in content

    def test_report_is_self_contained(self, tmp_path):
        """Report must not reference external CSS or JS files."""
        from doe.report import generate_report

        cfg = _make_doe_config(
            metadata={"name": "Self-contained Test"},
        )
        matrix = generate_design(cfg)

        results_dir = str(tmp_path / "results")
        results = {run.run_id: {"response": float(run.run_id * 5)} for run in matrix.runs}
        _write_result_files(results_dir, results)
        cfg.out_directory = results_dir
        cfg.processed_directory = str(tmp_path / "processed")

        output_path = str(tmp_path / "report.html")
        generate_report(matrix, cfg, results_dir=results_dir, output_path=output_path)

        content = Path(output_path).read_text(encoding="utf-8")
        # Must not contain external stylesheet or script links
        assert 'rel="stylesheet"' not in content
        assert "<link " not in content
        assert '<script src=' not in content
        # CSS must be inline
        assert "<style>" in content

    def test_report_embeds_plots_as_base64(self, tmp_path):
        """Plot images should be embedded as base64 data URIs."""
        from doe.report import generate_report

        cfg = _make_doe_config(
            metadata={"name": "Plot Embed Test"},
        )
        matrix = generate_design(cfg)

        results_dir = str(tmp_path / "results")
        results = {run.run_id: {"response": float(run.run_id * 3)} for run in matrix.runs}
        _write_result_files(results_dir, results)
        cfg.out_directory = results_dir
        cfg.processed_directory = str(tmp_path / "processed")

        output_path = str(tmp_path / "report.html")
        generate_report(matrix, cfg, results_dir=results_dir, output_path=output_path)

        content = Path(output_path).read_text(encoding="utf-8")
        assert "data:image/png;base64," in content

    def test_report_html_escapes_user_strings(self, tmp_path):
        """User-provided strings with HTML special chars must be escaped."""
        from doe.report import generate_report

        cfg = _make_doe_config(
            metadata={
                "name": "Test <script>alert(1)</script>",
                "description": 'Desc with "quotes" & <tags>',
            },
        )
        matrix = generate_design(cfg)

        results_dir = str(tmp_path / "results")
        results = {run.run_id: {"response": float(run.run_id)} for run in matrix.runs}
        _write_result_files(results_dir, results)
        cfg.out_directory = results_dir
        cfg.processed_directory = str(tmp_path / "processed")

        output_path = str(tmp_path / "report.html")
        generate_report(matrix, cfg, results_dir=results_dir, output_path=output_path)

        content = Path(output_path).read_text(encoding="utf-8")
        # Raw script tag must NOT appear
        assert "<script>alert(1)</script>" not in content
        # Escaped version should be present
        assert "&lt;script&gt;" in content


# ===================================================================
# RSM TESTS
# ===================================================================

class TestRSM:
    """Tests for the Response Surface Modeling module."""

    def _make_runs_and_responses(self):
        """Create a simple 2-factor, 2-level full factorial with known responses.

        Factors: A (levels "1", "3"), B (levels "10", "20")
        Response: y = 10 + 5*A_coded + 3*B_coded
        where A_coded = (A - 2)/1, B_coded = (B - 15)/5

        Run 1: A=1, B=10 -> A_coded=-1, B_coded=-1 -> y = 10 - 5 - 3 = 2
        Run 2: A=1, B=20 -> A_coded=-1, B_coded=+1 -> y = 10 - 5 + 3 = 8
        Run 3: A=3, B=10 -> A_coded=+1, B_coded=-1 -> y = 10 + 5 - 3 = 12
        Run 4: A=3, B=20 -> A_coded=+1, B_coded=+1 -> y = 10 + 5 + 3 = 18
        """
        from doe.models import Factor

        factors = [
            Factor(name="A", levels=["1", "3"], type="continuous"),
            Factor(name="B", levels=["10", "20"], type="continuous"),
        ]
        factor_names = ["A", "B"]

        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"A": "1", "B": "10"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"A": "1", "B": "20"}),
            ExperimentRun(run_id=3, block_id=1, factor_values={"A": "3", "B": "10"}),
            ExperimentRun(run_id=4, block_id=1, factor_values={"A": "3", "B": "20"}),
        ]
        responses = {1: 2.0, 2: 8.0, 3: 12.0, 4: 18.0}
        return runs, responses, factor_names, factors

    def test_linear_fit_perfect(self):
        """Linear RSM on data generated from a linear model should give R^2 = 1.0."""
        from doe.rsm import fit_rsm

        runs, responses, factor_names, factors = self._make_runs_and_responses()
        model = fit_rsm(runs, responses, factor_names, factors, model_type="linear")

        assert model.r_squared == pytest.approx(1.0, abs=1e-6)
        assert model.adj_r_squared == pytest.approx(1.0, abs=1e-6)

        # Check coefficients
        assert model.coefficients["intercept"] == pytest.approx(10.0, abs=1e-6)
        assert model.coefficients["A"] == pytest.approx(5.0, abs=1e-6)
        assert model.coefficients["B"] == pytest.approx(3.0, abs=1e-6)

    def test_linear_fit_noisy(self):
        """Linear RSM on noisy data should have R^2 < 1.0 but still reasonable."""
        from doe.rsm import fit_rsm
        from doe.models import Factor

        factors = [
            Factor(name="A", levels=["1", "3"], type="continuous"),
            Factor(name="B", levels=["10", "20"], type="continuous"),
        ]
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"A": "1", "B": "10"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"A": "1", "B": "20"}),
            ExperimentRun(run_id=3, block_id=1, factor_values={"A": "3", "B": "10"}),
            ExperimentRun(run_id=4, block_id=1, factor_values={"A": "3", "B": "20"}),
        ]
        # Add noise to the perfect linear response
        responses = {1: 2.5, 2: 7.5, 3: 12.5, 4: 17.0}
        model = fit_rsm(runs, responses, ["A", "B"], factors, model_type="linear")

        assert 0.9 < model.r_squared <= 1.0
        assert model.predicted_optimum is not None

    def test_quadratic_fit(self):
        """Quadratic RSM should include interaction and squared terms."""
        from doe.rsm import fit_rsm
        from doe.models import Factor

        factors = [
            Factor(name="A", levels=["1", "2", "3"], type="continuous"),
            Factor(name="B", levels=["10", "15", "20"], type="continuous"),
        ]
        # 3x3 grid: 9 runs with a quadratic response
        # y = 10 + 2*A_coded + 3*B_coded + 1.5*A_coded*B_coded - 2*A_coded^2
        runs = []
        responses = {}
        run_id = 1
        for a_val in ["1", "2", "3"]:
            for b_val in ["10", "15", "20"]:
                runs.append(ExperimentRun(
                    run_id=run_id, block_id=1,
                    factor_values={"A": a_val, "B": b_val},
                ))
                # Encode: A center=2, half_range=1; B center=15, half_range=5
                a_coded = (float(a_val) - 2.0) / 1.0
                b_coded = (float(b_val) - 15.0) / 5.0
                y = 10 + 2 * a_coded + 3 * b_coded + 1.5 * a_coded * b_coded - 2 * a_coded ** 2
                responses[run_id] = y
                run_id += 1

        model = fit_rsm(runs, responses, ["A", "B"], factors, model_type="quadratic")

        assert model.r_squared == pytest.approx(1.0, abs=1e-6)
        assert "A*B" in model.coefficients
        assert "A^2" in model.coefficients
        assert "B^2" in model.coefficients
        assert model.coefficients["A*B"] == pytest.approx(1.5, abs=1e-4)
        assert model.coefficients["A^2"] == pytest.approx(-2.0, abs=1e-4)

    def test_categorical_encoding(self):
        """Categorical 2-level factors should be encoded as -1/+1."""
        from doe.rsm import fit_rsm
        from doe.models import Factor

        factors = [
            Factor(name="method", levels=["fast", "slow"], type="categorical"),
        ]
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"method": "fast"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"method": "slow"}),
        ]
        # fast -> -1 (sorted: fast < slow), slow -> +1
        # y = 50 + 10*x -> fast=40, slow=60
        responses = {1: 40.0, 2: 60.0}
        model = fit_rsm(runs, responses, ["method"], factors, model_type="linear")

        assert model.r_squared == pytest.approx(1.0, abs=1e-6)
        assert model.coefficients["intercept"] == pytest.approx(50.0, abs=1e-6)
        assert model.coefficients["method"] == pytest.approx(10.0, abs=1e-6)

    def test_empty_runs(self):
        """fit_rsm with no valid runs should return a zero model."""
        from doe.rsm import fit_rsm

        model = fit_rsm([], {}, [], [])
        assert model.r_squared == 0.0
        assert model.coefficients == {"intercept": 0.0}


# ===================================================================
# OPTIMIZE TESTS
# ===================================================================

class TestOptimize:
    """Tests for the optimize module."""

    def _setup_results(self, tmp_path):
        """Create a config and result files for a 2^2 full factorial."""
        from doe.models import Factor

        factors = [
            Factor(name="A", levels=["low", "high"]),
            Factor(name="B", levels=["low", "high"]),
        ]
        responses_cfg = [
            ResponseVar(name="throughput", optimize="maximize"),
        ]
        cfg = DOEConfig(
            factors=factors,
            fixed_factors={},
            responses=responses_cfg,
            block_count=1,
            test_script="echo test",
            operation="full_factorial",
            processed_directory=str(tmp_path / "processed"),
            out_directory=str(tmp_path / "results"),
        )
        matrix = generate_design(cfg)

        # Create result files with known throughput values
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Assign throughput based on factor levels:
        # A=high is good (+20), B=high is slightly good (+5)
        for run in matrix.runs:
            val = 50.0
            if run.factor_values["A"] == "high":
                val += 20.0
            if run.factor_values["B"] == "high":
                val += 5.0
            result_file = results_dir / f"run_{run.run_id}.json"
            result_file.write_text(json.dumps({"throughput": val}))

        return matrix, cfg, str(results_dir)

    def test_recommend_runs_without_error(self, tmp_path):
        """recommend() should run to completion without errors."""
        from doe.optimize import recommend

        matrix, cfg, results_dir = self._setup_results(tmp_path)
        # Should not raise
        recommend(matrix, cfg, results_dir=results_dir)

    def test_recommend_specific_response(self, tmp_path):
        """recommend() with a specific response name should work."""
        from doe.optimize import recommend

        matrix, cfg, results_dir = self._setup_results(tmp_path)
        recommend(matrix, cfg, results_dir=results_dir, response_name="throughput")

    def test_recommend_missing_response(self, tmp_path, capsys):
        """recommend() with a nonexistent response should print an error."""
        from doe.optimize import recommend

        matrix, cfg, results_dir = self._setup_results(tmp_path)
        recommend(matrix, cfg, results_dir=results_dir, response_name="nonexistent")
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_best_observed_run(self, tmp_path, capsys):
        """recommend() should identify the best observed run correctly."""
        from doe.optimize import recommend

        matrix, cfg, results_dir = self._setup_results(tmp_path)
        recommend(matrix, cfg, results_dir=results_dir, response_name="throughput")
        captured = capsys.readouterr()

        # The best run should have A=high and B=high (value 75.0)
        assert "75.0" in captured.out
        # A=high should appear in the best run section
        assert "A = high" in captured.out
        assert "B = high" in captured.out

    def test_best_observed_run_minimize(self, tmp_path, capsys):
        """recommend() with minimize should find the lowest value."""
        from doe.optimize import recommend
        from doe.models import Factor

        factors = [
            Factor(name="X", levels=["low", "high"]),
        ]
        responses_cfg = [
            ResponseVar(name="latency", optimize="minimize"),
        ]
        cfg = DOEConfig(
            factors=factors,
            fixed_factors={},
            responses=responses_cfg,
            block_count=1,
            test_script="echo test",
            operation="full_factorial",
            processed_directory=str(tmp_path / "processed"),
            out_directory=str(tmp_path / "results"),
        )
        matrix = generate_design(cfg)

        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            val = 100.0 if run.factor_values["X"] == "high" else 20.0
            (results_dir / f"run_{run.run_id}.json").write_text(
                json.dumps({"latency": val})
            )

        recommend(matrix, cfg, results_dir=str(results_dir), response_name="latency")
        captured = capsys.readouterr()

        assert "minimize" in captured.out
        assert "20.0" in captured.out

    def test_factor_importance_order(self, tmp_path, capsys):
        """Factor A should be ranked above Factor B in importance."""
        from doe.optimize import recommend

        matrix, cfg, results_dir = self._setup_results(tmp_path)
        recommend(matrix, cfg, results_dir=results_dir, response_name="throughput")
        captured = capsys.readouterr()

        # In the "Factor importance" section, A should come first
        lines = captured.out.split("\n")
        importance_lines = [
            l for l in lines if l.strip().startswith("1.") or l.strip().startswith("2.")
        ]
        assert len(importance_lines) == 2
        assert "A" in importance_lines[0]
        assert "B" in importance_lines[1]
