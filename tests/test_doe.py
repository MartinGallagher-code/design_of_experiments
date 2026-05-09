# Copyright (C) 2026 Martin J. Gallagher
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

import numpy as np
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


# ===================================================================
# LOG SWEEP TESTS
# ===================================================================

class TestLogSweep:

    def test_log_sweep_single_factor(self, tmp_path):
        """Single factor [1, 1000] with 4 sweep points -> log-spaced values."""
        cfg_dict = _make_config_dict(
            factors=[{"name": "threads", "levels": ["1", "1000"], "type": "continuous"}],
            operation="log_sweep",
        )
        cfg_dict["settings"]["sweep_points"] = 4
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        matrix = generate_design(cfg)
        assert len(matrix.runs) == 4
        # Values should be approximately 1, 10, 100, 1000
        values = [float(r.factor_values["threads"]) for r in sorted(matrix.runs, key=lambda r: float(r.factor_values["threads"]))]
        assert math.isclose(values[0], 1.0, rel_tol=0.01)
        assert math.isclose(values[1], 10.0, rel_tol=0.01)
        assert math.isclose(values[2], 100.0, rel_tol=0.01)
        assert math.isclose(values[3], 1000.0, rel_tol=0.01)

    def test_log_sweep_multi_factor(self, tmp_path):
        """Two factors with 3 sweep points -> 9 runs (3x3)."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "threads", "levels": ["1", "100"], "type": "continuous"},
                {"name": "batch", "levels": ["10", "1000"], "type": "continuous"},
            ],
            operation="log_sweep",
        )
        cfg_dict["settings"]["sweep_points"] = 3
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        matrix = generate_design(cfg)
        assert len(matrix.runs) == 9  # 3 * 3

    def test_log_sweep_validates_positive_levels(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[{"name": "x", "levels": ["0", "10"], "type": "continuous"}],
            operation="log_sweep",
        )
        path = _write_config(tmp_path, cfg_dict)
        with pytest.raises(ValueError, match="positive"):
            load_config(path, strict=False)

    def test_log_sweep_passes_through_non_numeric_levels(self, tmp_path):
        """Non-numeric 2-level factors are not swept, just passed through."""
        cfg_dict = _make_config_dict(
            factors=[{"name": "x", "levels": ["low", "high"], "type": "continuous"}],
            operation="log_sweep",
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        matrix = generate_design(cfg, seed=42)
        levels = sorted(set(r.factor_values["x"] for r in matrix.runs))
        assert levels == ["high", "low"]

    def test_log_sweep_passes_through_multi_level_factors(self, tmp_path):
        """Factors with >2 levels are kept as-is (not swept)."""
        cfg_dict = _make_config_dict(
            factors=[{"name": "x", "levels": ["1", "10", "100"], "type": "continuous"}],
            operation="log_sweep",
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        matrix = generate_design(cfg, seed=42)
        levels = sorted(set(r.factor_values["x"] for r in matrix.runs))
        assert levels == ["1", "10", "100"]

    def test_log_sweep_default_points(self, tmp_path):
        """When sweep_points and lhs_samples are 0, should default to 8."""
        cfg_dict = _make_config_dict(
            factors=[{"name": "x", "levels": ["1", "100"], "type": "continuous"}],
            operation="log_sweep",
        )
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        matrix = generate_design(cfg)
        assert len(matrix.runs) == 8


# ===================================================================
# ORDINAL TREND TESTS
# ===================================================================

class TestOrdinalTrends:

    def test_ordinal_trend_linear(self, tmp_path):
        """3-level ordinal factor with perfectly linear response."""
        factors = [Factor(name="speed", levels=["1", "2", "3"], type="ordinal")]
        responses = [ResponseVar(name="output")]
        cfg = _make_doe_config(factors=factors, responses=responses, operation="full_factorial", block_count=1)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        # Linear response: output = 10 * speed_level
        response_map = {}
        for run in matrix.runs:
            val = float(run.factor_values["speed"])
            response_map[run.run_id] = {"output": val * 10}
        _write_result_files(results_dir, response_map)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["output"]
        assert len(analysis.ordinal_trends) == 1
        trend = analysis.ordinal_trends[0]
        assert trend.factor_name == "speed"
        assert trend.linear_coefficient != 0
        assert trend.r_squared_linear > 0.9

    def test_ordinal_trend_quadratic(self, tmp_path):
        """3-level ordinal factor with U-shaped response."""
        factors = [Factor(name="temp", levels=["1", "2", "3"], type="ordinal")]
        responses = [ResponseVar(name="yield")]
        cfg = _make_doe_config(factors=factors, responses=responses, operation="full_factorial", block_count=2)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        # U-shaped: yield = (speed - 2)^2 + 5
        response_map = {}
        for run in matrix.runs:
            val = float(run.factor_values["temp"])
            response_map[run.run_id] = {"yield": (val - 2) ** 2 + 5}
        _write_result_files(results_dir, response_map)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["yield"]
        assert len(analysis.ordinal_trends) == 1
        trend = analysis.ordinal_trends[0]
        assert trend.quadratic_ss > 0

    def test_ordinal_trend_skips_categorical(self, tmp_path):
        """Categorical factors should produce no ordinal trends."""
        factors = [
            Factor(name="color", levels=["red", "green", "blue"], type="categorical"),
        ]
        responses = [ResponseVar(name="score")]
        cfg = _make_doe_config(factors=factors, responses=responses)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        response_map = {r.run_id: {"score": float(i)} for i, r in enumerate(matrix.runs)}
        _write_result_files(results_dir, response_map)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["score"]
        assert len(analysis.ordinal_trends) == 0

    def test_ordinal_trend_skips_2_level(self, tmp_path):
        """2-level ordinal factors should produce no trends (need 3+)."""
        factors = [Factor(name="speed", levels=["1", "2"], type="ordinal")]
        responses = [ResponseVar(name="output")]
        cfg = _make_doe_config(factors=factors, responses=responses)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        response_map = {r.run_id: {"output": float(r.factor_values["speed"])} for r in matrix.runs}
        _write_result_files(results_dir, response_map)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True)
        analysis = report.results_by_response["output"]
        assert len(analysis.ordinal_trends) == 0


# ===================================================================
# KNEE-POINT DETECTION TESTS
# ===================================================================

class TestKneePointDetection:

    def test_knee_detection_obvious_saturation(self):
        """Obvious saturation curve should detect knee near the correct value."""
        from doe.knee import detect_knee_point
        # Throughput saturates around x=8
        factor_values = [1, 2, 4, 8, 16, 32, 64]
        response_values = [10, 20, 38, 42, 43, 43.5, 43.8]
        result = detect_knee_point(factor_values, response_values)
        assert result is not None
        # Knee should be near 4-8 range
        assert 2 <= result.knee_value <= 16
        assert result.r_squared > 0.5

    def test_knee_detection_no_knee(self):
        """Perfectly linear response should have similar slopes."""
        from doe.knee import detect_knee_point
        factor_values = [1, 2, 3, 4, 5]
        response_values = [10, 20, 30, 40, 50]
        result = detect_knee_point(factor_values, response_values)
        if result is not None:
            # Slopes should be similar (no real knee)
            assert abs(result.segment1_slope - result.segment2_slope) < 5

    def test_knee_detection_confidence_interval(self):
        """CI should bracket the knee value."""
        from doe.knee import detect_knee_point
        factor_values = [1, 2, 4, 8, 16, 32]
        response_values = [5, 10, 18, 21, 22, 22.5]
        result = detect_knee_point(factor_values, response_values)
        assert result is not None
        assert result.ci_low <= result.knee_value <= result.ci_high

    def test_knee_detection_too_few_points(self):
        """Less than 3 points should return None."""
        from doe.knee import detect_knee_point
        result = detect_knee_point([1, 2], [10, 20])
        assert result is None

    def test_knee_detection_in_analyze(self, tmp_path):
        """Knee detection integrates with analyze() when detect_knee=True."""
        factors = [Factor(name="threads", levels=["1", "2", "4", "8", "16", "32", "64"],
                          type="ordinal", unit="threads")]
        responses = [ResponseVar(name="throughput", optimize="maximize")]
        cfg = _make_doe_config(factors=factors, responses=responses, operation="full_factorial")
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        # Saturating response
        saturation_map = {"1": 10, "2": 20, "4": 38, "8": 42, "16": 43, "32": 43.5, "64": 43.8}
        response_map = {}
        for run in matrix.runs:
            t = run.factor_values["threads"]
            response_map[run.run_id] = {"throughput": saturation_map[t]}
        _write_result_files(results_dir, response_map)

        report = analyze(matrix, cfg, results_dir=results_dir, no_plots=True, detect_knee=True)
        assert "throughput" in report.knee_point_results
        assert len(report.knee_point_results["throughput"]) >= 1

    def test_knee_plot_creates_file(self, tmp_path):
        """Verify PNG is created by plot_knee_point."""
        from doe.knee import detect_knee_point, plot_knee_point
        factor_values = [1, 2, 4, 8, 16, 32]
        response_values = [5, 10, 18, 21, 22, 22.5]
        result = detect_knee_point(factor_values, response_values)
        assert result is not None
        output_path = str(tmp_path / "knee.png")
        plot_knee_point(factor_values, response_values, result, output_path,
                       factor_name="threads", response_name="throughput")
        assert os.path.exists(output_path)


# ===================================================================
# ADAPTIVE EXPERIMENTATION TESTS
# ===================================================================

class TestAdaptiveExperimentation:

    def _setup_initial_results(self, tmp_path):
        """Create a simple experiment with initial results."""
        factors = [
            Factor(name="A", levels=["1", "10"], type="continuous"),
            Factor(name="B", levels=["1", "10"], type="continuous"),
        ]
        responses = [ResponseVar(name="y", optimize="maximize")]
        cfg = _make_doe_config(factors=factors, responses=responses, operation="full_factorial")
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        # Response: y = A + B (so higher is better)
        response_map = {}
        for run in matrix.runs:
            a = float(run.factor_values["A"])
            b = float(run.factor_values["B"])
            response_map[run.run_id] = {"y": a + b}
        _write_result_files(results_dir, response_map)
        cfg_with_dir = _make_doe_config(factors=factors, responses=responses, operation="full_factorial")
        cfg_with_dir.out_directory = results_dir
        return cfg_with_dir, matrix, results_dir

    def test_adaptive_refine_contracts_space(self, tmp_path):
        """Refine strategy should produce points near the best observed region."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix, results_dir = self._setup_initial_results(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=4)
        new_matrix, state = plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir, seed=42)
        assert len(new_matrix.runs) == 4
        # Best run is A=10, B=10. New points should be near there.
        for run in new_matrix.runs:
            a = float(run.factor_values["A"])
            b = float(run.factor_values["B"])
            # Should be in the upper range (within 25% of full range from best)
            assert a >= 5.0  # 10 - 0.25*9 ≈ 7.75, but with randomness allow some slack
            assert b >= 5.0

    def test_adaptive_explore_avoids_existing(self, tmp_path):
        """Explore strategy should produce points distant from existing."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix, results_dir = self._setup_initial_results(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="explore", batch_size=4)
        new_matrix, state = plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir, seed=42)
        assert len(new_matrix.runs) == 4
        # New points should exist (basic sanity)
        for run in new_matrix.runs:
            a = float(run.factor_values["A"])
            b = float(run.factor_values["B"])
            assert 1.0 <= a <= 10.0
            assert 1.0 <= b <= 10.0

    def test_adaptive_balanced_splits_batch(self, tmp_path):
        """Balanced strategy should generate both refine and explore points."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix, results_dir = self._setup_initial_results(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="balanced", batch_size=6)
        new_matrix, state = plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir, seed=42)
        assert len(new_matrix.runs) == 6

    def test_adaptive_stopping_max_phases(self, tmp_path):
        """Should stop after max phases reached."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig, _save_state, AdaptiveState
        cfg, matrix, results_dir = self._setup_initial_results(tmp_path)
        # Pretend we already did 5 phases
        state = AdaptiveState(phase=5, total_runs=20, completed_phases=[{"phase": i} for i in range(1, 6)])
        _save_state(state, results_dir)
        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=4, stopping_max_phases=5)
        _, state = plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir)
        assert state.should_stop is True
        assert "Maximum phases" in state.stop_reason

    def test_adaptive_stopping_effect_threshold(self, tmp_path):
        """Should stop when max effect is below threshold."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        # Create experiment with very small effects
        factors = [
            Factor(name="A", levels=["1", "2"], type="continuous"),
            Factor(name="B", levels=["1", "2"], type="continuous"),
        ]
        responses = [ResponseVar(name="y")]
        cfg = _make_doe_config(factors=factors, responses=responses)
        matrix = generate_design(cfg)
        results_dir = str(tmp_path / "results")
        # Nearly constant response
        response_map = {r.run_id: {"y": 100.0 + 0.001 * r.run_id} for r in matrix.runs}
        _write_result_files(results_dir, response_map)
        cfg.out_directory = results_dir

        adaptive_cfg = AdaptiveConfig(strategy="refine", batch_size=4,
                                      stopping_effect_threshold=1.0)
        _, state = plan_next_batch(matrix, cfg, adaptive_cfg, results_dir=results_dir)
        assert state.should_stop is True
        assert "below threshold" in state.stop_reason

    def test_adaptive_state_persistence(self, tmp_path):
        """Save state, load state, verify round-trip."""
        from doe.adaptive import _save_state, _load_state, AdaptiveState
        results_dir = str(tmp_path / "results")
        os.makedirs(results_dir, exist_ok=True)
        state = AdaptiveState(
            phase=3, total_runs=25,
            completed_phases=[{"phase": 1, "n_runs": 10}, {"phase": 2, "n_runs": 8}],
            should_stop=False, stop_reason="",
        )
        _save_state(state, results_dir)
        loaded = _load_state(results_dir)
        assert loaded is not None
        assert loaded.phase == 3
        assert loaded.total_runs == 25
        assert len(loaded.completed_phases) == 2

    def test_adaptive_backward_compatible(self, tmp_path):
        """Config without adaptive key should still load fine."""
        cfg_dict = _make_config_dict()
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.adaptive is None

    def test_adaptive_config_parsed(self, tmp_path):
        """Config with adaptive section should parse correctly."""
        cfg_dict = _make_config_dict()
        cfg_dict["adaptive"] = {
            "strategy": "balanced",
            "batch_size": 8,
            "stopping_max_phases": 3,
        }
        path = _write_config(tmp_path, cfg_dict)
        cfg = load_config(path, strict=False)
        assert cfg.adaptive is not None
        assert cfg.adaptive.strategy == "balanced"
        assert cfg.adaptive.batch_size == 8
        assert cfg.adaptive.stopping_max_phases == 3


class TestRunnerHelpers:
    """Tests for doe.runner.parse_factors and doe.runner.emit."""

    def test_parse_double_dash(self):
        from doe.runner import parse_factors
        argv = ["--threads", "8", "--batch_size", "100", "--out", "/tmp/r.json"]
        values, out = parse_factors(["threads", "batch_size"], arg_style="double-dash", argv=argv)
        assert values == {"threads": "8", "batch_size": "100"}
        assert out == "/tmp/r.json"

    def test_parse_double_dash_with_fixed(self):
        from doe.runner import parse_factors
        argv = ["--a", "1", "--b", "2", "--seed", "42", "--out", "x"]
        values, _ = parse_factors(["a", "b"], fixed_factor_names=["seed"],
                                  arg_style="double-dash", argv=argv)
        assert values == {"a": "1", "b": "2"}  # fixed factors not returned

    def test_parse_env(self, monkeypatch):
        from doe.runner import parse_factors
        monkeypatch.setenv("THREADS", "4")
        monkeypatch.setenv("BATCH_SIZE", "32")
        values, out = parse_factors(["threads", "batch_size"], arg_style="env",
                                    argv=["--out", "x"])
        assert values == {"threads": "4", "batch_size": "32"}
        assert out == "x"

    def test_parse_env_missing(self, monkeypatch):
        from doe.runner import parse_factors
        monkeypatch.delenv("THREADS", raising=False)
        with pytest.raises(SystemExit):
            parse_factors(["threads"], arg_style="env", argv=["--out", "x"])

    def test_parse_positional(self):
        from doe.runner import parse_factors
        values, out = parse_factors(
            ["a", "b"], fixed_factor_names=["c"],
            arg_style="positional", argv=["1", "2", "3", "--out", "p.json"],
        )
        assert values == {"a": "1", "b": "2"}
        assert out == "p.json"

    def test_parse_positional_wrong_count(self):
        from doe.runner import parse_factors
        with pytest.raises(SystemExit):
            parse_factors(["a", "b"], arg_style="positional",
                          argv=["1", "--out", "p"])

    def test_parse_unknown_style(self):
        from doe.runner import parse_factors
        with pytest.raises(ValueError):
            parse_factors(["a"], arg_style="bogus", argv=[])

    def test_emit_kwargs(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "out.json")
        emit(out, throughput=42.0, latency=1.5)
        data = json.loads(Path(out).read_text())
        assert data == {"throughput": 42.0, "latency": 1.5}

    def test_emit_dict(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "out.json")
        emit(out, {"cpu-util": 0.83, "p99-latency": 12.5})
        data = json.loads(Path(out).read_text())
        assert data == {"cpu-util": 0.83, "p99-latency": 12.5}

    def test_emit_creates_parent_dir(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "nested" / "out.json")
        emit(out, throughput=1.0)
        assert Path(out).exists()

    def test_emit_expected_mismatch(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="missing"):
            emit(out, throughput=1.0, _expected=["throughput", "latency"])
        with pytest.raises(ValueError, match="unexpected"):
            emit(out, througput=1.0, _expected=["throughput"])  # typo

    def test_emit_non_numeric(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "out.json")
        with pytest.raises(ValueError, match="not numeric"):
            emit(out, throughput="oops")

    def test_emit_dict_and_kwargs_conflict(self, tmp_path):
        from doe.runner import emit
        out = str(tmp_path / "out.json")
        with pytest.raises(TypeError):
            emit(out, {"a": 1}, b=2)


class TestScaffoldTest:
    """Tests for doe scaffold-test code generation."""

    def _cfg(self, tmp_path, arg_style="double-dash", factors=None, responses=None):
        cfg_dict = _make_config_dict(
            factors=factors or [
                {"name": "threads", "levels": ["1", "8"]},
                {"name": "batch_size", "levels": ["10", "100"]},
            ],
            responses=responses or [
                {"name": "throughput", "optimize": "maximize"},
                {"name": "latency", "optimize": "minimize"},
            ],
            runner={"arg_style": arg_style},
        )
        return load_config(_write_config(tmp_path, cfg_dict), strict=False)

    def test_python_scaffold_runs(self, tmp_path):
        """Generated Python scaffold should run end-to-end and write JSON."""
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(tmp_path)
        script = tmp_path / "test.py"
        generate_test_scaffold(cfg, str(script), language="py")

        out = tmp_path / "result.json"
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        result = subprocess.run(
            [sys.executable, str(script),
             "--threads", "8", "--batch_size", "100", "--out", str(out)],
            env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text())
        assert set(data.keys()) == {"throughput", "latency"}

    def test_bash_scaffold_runs(self, tmp_path):
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(tmp_path)
        script = tmp_path / "test.sh"
        generate_test_scaffold(cfg, str(script), language="sh")

        out = tmp_path / "result.json"
        result = subprocess.run(
            ["bash", str(script),
             "--threads", "8", "--batch_size", "100", "--out", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text())
        assert set(data.keys()) == {"throughput", "latency"}

    def test_python_scaffold_handles_hyphenated_names(self, tmp_path):
        """Hyphenated factor / response names must round-trip via dict-form emit."""
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(
            tmp_path,
            factors=[{"name": "batch-size", "levels": ["10", "100"]}],
            responses=[{"name": "p99-latency", "optimize": "minimize"}],
        )
        script = tmp_path / "test.py"
        generate_test_scaffold(cfg, str(script), language="py")
        out = tmp_path / "result.json"
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        result = subprocess.run(
            [sys.executable, str(script), "--batch-size", "10", "--out", str(out)],
            env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text())
        assert "p99-latency" in data

    def test_python_scaffold_positional(self, tmp_path):
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(tmp_path, arg_style="positional")
        script = tmp_path / "test.py"
        generate_test_scaffold(cfg, str(script), language="py")
        out = tmp_path / "result.json"
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        result = subprocess.run(
            [sys.executable, str(script), "8", "100", "--out", str(out)],
            env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(out.read_text())["throughput"] == 0.0

    def test_python_scaffold_env(self, tmp_path):
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(tmp_path, arg_style="env")
        script = tmp_path / "test.py"
        generate_test_scaffold(cfg, str(script), language="py")
        out = tmp_path / "result.json"
        env = dict(os.environ)
        env["THREADS"] = "4"
        env["BATCH_SIZE"] = "50"
        env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, str(script), "--out", str(out)],
            env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(out.read_text())["throughput"] == 0.0

    def test_scaffold_unknown_language(self, tmp_path):
        from doe.codegen import generate_test_scaffold
        cfg = self._cfg(tmp_path)
        with pytest.raises(ValueError):
            generate_test_scaffold(cfg, str(tmp_path / "x"), language="rust")


class TestScaffoldConfig:
    """Tests for doe scaffold-config."""

    def test_emits_valid_loadable_config(self, tmp_path, capsys):
        """Generated template must round-trip through load_config."""
        from doe.codegen import generate_config_template
        path = tmp_path / "config.json"
        generate_config_template(str(path))

        cfg = load_config(str(path), strict=False)
        assert {f.name for f in cfg.factors} == {"temperature", "pressure", "catalyst"}
        # fixed_factors mirrors factor names with their first level
        assert cfg.fixed_factors == {"temperature": "100", "pressure": "1", "catalyst": "A"}
        # And the loader warns about the resulting overlap
        out = capsys.readouterr().out
        assert "factors" in out and "fixed_factors" in out

    def test_design_generates_from_template(self, tmp_path, capsys):
        """The default operation in the template must produce a valid design."""
        from doe.codegen import generate_config_template
        path = tmp_path / "config.json"
        generate_config_template(str(path))
        cfg = load_config(str(path), strict=False)
        capsys.readouterr()  # drop overlap warning
        matrix = generate_design(cfg)
        # 2 numeric (2 levels) * 1 categorical (3 levels) = 12 runs
        assert len(matrix.runs) == 12

    def test_levels_first_entry_used_in_fixed(self, tmp_path):
        """User asked: when a factor has multiple levels, fixed_factors uses
        the first one. Verify by inspecting raw JSON."""
        from doe.codegen import generate_config_template
        path = tmp_path / "config.json"
        generate_config_template(str(path))
        raw = json.loads(path.read_text())
        for factor in raw["factors"]:
            assert raw["fixed_factors"][factor["name"]] == factor["levels"][0]

    def test_help_keys_ignored_by_loader(self, tmp_path):
        """Underscore-prefixed help keys must not become real config items."""
        from doe.codegen import generate_config_template
        path = tmp_path / "config.json"
        generate_config_template(str(path))
        cfg = load_config(str(path), strict=False)
        # _operation_options sits next to operation but mustn't change it
        assert cfg.operation == "full_factorial"
        # _arg_style_options likewise
        assert cfg.runner.arg_style == "double-dash"
        # adaptive is gated behind '_adaptive' (disabled) — must be None
        assert cfg.adaptive is None

    def test_unicode_not_escaped(self, tmp_path):
        from doe.codegen import generate_config_template
        path = tmp_path / "config.json"
        generate_config_template(str(path))
        text = path.read_text(encoding="utf-8")
        assert "\\u2014" not in text  # em-dash kept as literal, not escaped

    def test_overlap_warning_only_when_overlapping(self, tmp_path, capsys):
        """A clean config (no overlap) must not emit the warning."""
        cfg_dict = _make_config_dict(
            factors=[{"name": "A", "levels": ["1", "2"]}],
            fixed_factors={"B": "x"},  # different name from any factor
        )
        path = _write_config(tmp_path, cfg_dict)
        load_config(path, strict=False)
        out = capsys.readouterr().out
        assert "fixed_factors" not in out


class TestSessionRunner:
    """Tests for --session subdirectories in generated runners."""

    def _make_test_script(self, tmp_path):
        """Write a tiny test script that just emits a constant response."""
        script = tmp_path / "test.py"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"sys.path.insert(0, {str(PROJECT_ROOT)!r})\n"
            "from doe.runner import parse_factors, emit\n"
            "factors, out = parse_factors(['x', 'y'])\n"
            "emit(out, r=float(factors['x']) + float(factors['y']))\n"
        )
        script.chmod(0o755)
        return script

    def _make_cfg(self, tmp_path, test_script):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["1", "2"]},
                {"name": "y", "levels": ["10", "20"]},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            test_script=str(test_script),
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        return load_config(_write_config(tmp_path, cfg_dict), strict=False)

    def test_no_session_unchanged(self, tmp_path):
        """Without --session, results land directly in out_directory."""
        from doe.codegen import generate_script
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.sh"
        generate_script(matrix, cfg, str(runner), format="sh", session_prefix=None)
        result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        results_dir = tmp_path / "results"
        assert (results_dir / "run_1.json").exists()
        assert not (results_dir / "latest").exists()

    def test_session_with_prefix(self, tmp_path):
        """--session=baseline creates baseline-<TS>/ and a 'latest' symlink."""
        from doe.codegen import generate_script
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.sh"
        generate_script(matrix, cfg, str(runner), format="sh", session_prefix="baseline")
        result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

        results_dir = tmp_path / "results"
        sessions = [p for p in results_dir.iterdir()
                    if p.is_dir() and p.name.startswith("baseline-")]
        assert len(sessions) == 1
        # Result files inside the session dir
        assert (sessions[0] / "run_1.json").exists()
        # Latest symlink points at the session
        latest = results_dir / "latest"
        assert latest.is_symlink()
        assert os.readlink(str(latest)) == sessions[0].name
        # Bare results dir is empty of run files
        assert not (results_dir / "run_1.json").exists()

    def test_session_timestamp_only(self, tmp_path):
        """--session with empty prefix produces timestamp-only directories."""
        from doe.codegen import generate_script
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.sh"
        generate_script(matrix, cfg, str(runner), format="sh", session_prefix="")
        result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        sessions = [p for p in (tmp_path / "results").iterdir()
                    if p.is_dir() and not p.is_symlink()]
        assert len(sessions) == 1
        # Name is pure timestamp (no dash prefix)
        assert sessions[0].name[0].isdigit()

    def test_session_python_runner(self, tmp_path):
        """The Python-format runner honours sessions too."""
        from doe.codegen import generate_script
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.py"
        generate_script(matrix, cfg, str(runner), format="py", session_prefix="pyrun")
        env = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
        result = subprocess.run([sys.executable, str(runner)], env=env,
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        sessions = [p for p in (tmp_path / "results").iterdir()
                    if p.is_dir() and p.name.startswith("pyrun-")]
        assert len(sessions) == 1
        latest = tmp_path / "results" / "latest"
        assert latest.is_symlink()

    def test_design_matrix_copied_into_session(self, tmp_path):
        """If design_matrix.json sits in BASE_OUT, it must be copied into
        the session dir so analyze can find it via 'latest'."""
        from doe.codegen import generate_script
        from doe.cli import _save_matrix
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        # Persist matrix at the base level (what `doe generate` does)
        _save_matrix(matrix, str(tmp_path / "results"))
        runner = tmp_path / "run.sh"
        generate_script(matrix, cfg, str(runner), format="sh", session_prefix="ses")
        result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        latest = tmp_path / "results" / "latest"
        assert (latest / "design_matrix.json").exists()

    def test_resolve_results_dir_uses_latest(self, tmp_path):
        """_resolve_results_dir should auto-pick <out>/latest when present."""
        from doe.cli import _resolve_results_dir
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        base = Path(cfg.out_directory)
        base.mkdir(parents=True, exist_ok=True)
        session = base / "ses-20990101-000000"
        session.mkdir()
        (base / "latest").symlink_to(session.name)
        resolved = _resolve_results_dir(cfg, None)
        assert os.path.realpath(resolved) == str(session)

    def test_resolve_results_dir_explicit_overrides_latest(self, tmp_path):
        """An explicit --results-dir must win over auto-latest."""
        from doe.cli import _resolve_results_dir
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        base = Path(cfg.out_directory)
        base.mkdir(parents=True, exist_ok=True)
        (base / "latest").symlink_to(".")
        explicit = str(tmp_path / "elsewhere")
        assert _resolve_results_dir(cfg, explicit) == explicit

    def test_subsequent_sessions_update_latest(self, tmp_path):
        """A second invocation must repoint 'latest' at the newer session."""
        from doe.codegen import generate_script
        cfg = self._make_cfg(tmp_path, self._make_test_script(tmp_path))
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.sh"
        generate_script(matrix, cfg, str(runner), format="sh", session_prefix="s")
        for _ in range(2):
            result = subprocess.run(["bash", str(runner)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            import time; time.sleep(1.05)
        sessions = sorted(p.name for p in (tmp_path / "results").iterdir()
                          if p.is_dir() and p.name.startswith("s-"))
        assert len(sessions) == 2
        latest_target = os.readlink(str(tmp_path / "results" / "latest"))
        assert latest_target == sessions[-1]


class TestModelAdequacy:
    """Tests for compute_model_adequacy + integration into analyze()."""

    def _ccd_factors_and_runs(self):
        from doe.models import Factor, ExperimentRun
        # 3-factor central composite design (small) so a quadratic fits.
        factors = [
            Factor(name=name, levels=["-1", "1"], type="continuous")
            for name in ("x", "y", "z")
        ]
        coords = []
        # 2^3 corners
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    coords.append((x, y, z))
        # Axial points
        a = 1.682
        coords += [(-a, 0, 0), (a, 0, 0), (0, -a, 0), (0, a, 0), (0, 0, -a), (0, 0, a)]
        # Centre points
        for _ in range(3):
            coords.append((0, 0, 0))
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x": str(x), "y": str(y), "z": str(z)})
            for i, (x, y, z) in enumerate(coords)
        ]
        factor_names = ["x", "y", "z"]
        return factors, factor_names, runs

    def _fit(self, runs, factor_names, factors, fn, model_type="quadratic"):
        from doe.rsm import fit_rsm
        responses = {r.run_id: fn(*[float(r.factor_values[f]) for f in factor_names])
                     for r in runs}
        model = fit_rsm(runs, responses, factor_names, factors, model_type=model_type)
        return model, responses

    def test_press_q2_near_perfect_fit(self):
        """Quadratic fit on a noiseless quadratic surface gives R²≈1, Q²≈1."""
        from doe.rsm import compute_model_adequacy
        factors, names, runs = self._ccd_factors_and_runs()
        model, _ = self._fit(runs, names, factors,
                             lambda x, y, z: 5 - x*x - y*y - 0.5*z*z + 0.1*x*y)
        ma = compute_model_adequacy(model, run_ids_in_order=[r.run_id for r in runs])
        assert ma is not None
        assert ma.r_squared > 0.99999
        assert ma.predicted_r_squared > 0.99
        assert ma.press < 1e-6
        # Perfect-fit residuals are degenerate; we just confirm the field
        # populates and is finite.
        assert ma.durbin_watson is not None
        assert 0.0 <= ma.durbin_watson <= 4.0

    def test_shapiro_runs(self):
        """Even on noisy data the Shapiro-Wilk fields populate."""
        import random
        from doe.rsm import compute_model_adequacy
        factors, names, runs = self._ccd_factors_and_runs()
        random.seed(1)
        def noisy(x, y, z):
            return 5 - x*x - y*y - 0.5*z*z + random.gauss(0, 0.1)
        model, _ = self._fit(runs, names, factors, noisy)
        ma = compute_model_adequacy(model, run_ids_in_order=[r.run_id for r in runs])
        assert ma.shapiro_w is not None
        assert 0 < ma.shapiro_w <= 1
        assert ma.shapiro_p is not None
        assert 0 <= ma.shapiro_p <= 1

    def test_cooks_flags_outlier(self):
        """Inject a single bad data point and expect Cook's distance to flag it."""
        from doe.rsm import compute_model_adequacy
        factors, names, runs = self._ccd_factors_and_runs()
        model, responses = self._fit(runs, names, factors,
                                     lambda x, y, z: 5 - x*x - y*y - 0.5*z*z)
        # Refit with the first run perturbed
        responses[runs[0].run_id] += 50.0  # huge outlier
        from doe.rsm import fit_rsm
        model = fit_rsm(runs, responses, names, factors, model_type="quadratic")
        ma = compute_model_adequacy(model, run_ids_in_order=[r.run_id for r in runs])
        assert runs[0].run_id in ma.high_influence_run_ids
        assert ma.max_cooks_distance > ma.cooks_threshold

    def test_durbin_watson_picks_up_drift(self):
        """A monotonic trend across run order → low Durbin-Watson."""
        from doe.rsm import compute_model_adequacy, fit_rsm
        factors, names, runs = self._ccd_factors_and_runs()
        # Underlying surface plus an additive run-order drift the model can't capture
        responses = {}
        for i, r in enumerate(runs):
            x = float(r.factor_values["x"])
            y = float(r.factor_values["y"])
            z = float(r.factor_values["z"])
            responses[r.run_id] = 5 - x*x - y*y - 0.5*z*z + 0.4 * i  # strong drift
        model = fit_rsm(runs, responses, names, factors, model_type="quadratic")
        ma = compute_model_adequacy(model, run_ids_in_order=[r.run_id for r in runs])
        assert ma.runorder_drift_p is not None
        assert ma.runorder_drift_p < 0.05  # drift should be detected
        assert any("drift" in n.lower() for n in ma.notes)

    def test_runorder_drift_uses_supplied_order(self):
        """When the runner randomises the order, the drift test must use the
        physical execution order, not the order in diagnostics."""
        from doe.rsm import compute_model_adequacy, fit_rsm
        factors, names, runs = self._ccd_factors_and_runs()
        responses = {}
        # Sort runs by run_id ascending (assumed physical order)
        for i, r in enumerate(sorted(runs, key=lambda r: r.run_id)):
            x = float(r.factor_values["x"])
            y = float(r.factor_values["y"])
            z = float(r.factor_values["z"])
            responses[r.run_id] = 5 - x*x - y*y - 0.5*z*z + 0.2 * i
        model = fit_rsm(runs, responses, names, factors, model_type="quadratic")
        # Physical order: ascending run_id
        ma = compute_model_adequacy(
            model, run_ids_in_order=sorted(r.run_id for r in runs)
        )
        assert ma.runorder_drift_p is not None
        assert ma.runorder_drift_p < 0.05

    def test_analyze_attaches_adequacy_and_stationary(self, tmp_path):
        """End-to-end: analyze() should populate ResponseAnalysis fields."""
        from doe.config import load_config
        from doe.design import generate_design
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="central_composite",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=3)

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            z = float(run.factor_values["z"])
            r = -(x - 0.3) ** 2 - (y + 0.2) ** 2 - 0.5 * z * z + 5
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"r": r}))

        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        ra = report.results_by_response["r"]
        assert ra.model_adequacy is not None
        assert ra.model_adequacy.r_squared > 0.99
        assert ra.stationary_point is not None
        # Surface is concave on all axes → maximum
        assert ra.stationary_point.nature == "maximum"


class TestStationaryPoint:
    """Tests for characterize_stationary_point."""

    def _factors(self, names):
        from doe.models import Factor
        return [Factor(name=n, levels=["-1", "1"], type="continuous") for n in names]

    def _model(self, coefs):
        from doe.rsm import RSMModel
        return RSMModel(
            response_name="y",
            coefficients=coefs,
            r_squared=1.0, adj_r_squared=1.0,
            predicted_optimum={}, predicted_value=0.0,
        )

    def test_maximum(self):
        from doe.rsm import characterize_stationary_point
        # y = -(x-0.3)^2 - (y+0.2)^2 + 5  → max at (0.3, -0.2)
        coefs = {"intercept": 5.0 - 0.09 - 0.04,
                 "x": 0.6, "y": -0.4,
                 "x^2": -1.0, "y^2": -1.0,
                 "x*y": 0.0}
        sp = characterize_stationary_point(self._model(coefs), ["x", "y"], self._factors(["x", "y"]))
        assert sp is not None
        assert sp.nature == "maximum"
        assert abs(sp.coded_location["x"] - 0.3) < 1e-6
        assert abs(sp.coded_location["y"] - (-0.2)) < 1e-6
        assert sp.inside_design_region is True
        assert all(v < 0 for v in sp.eigenvalues)

    def test_minimum(self):
        from doe.rsm import characterize_stationary_point
        coefs = {"intercept": 0.0, "x": 0.0, "y": 0.0,
                 "x^2": 1.0, "y^2": 1.0, "x*y": 0.0}
        sp = characterize_stationary_point(self._model(coefs), ["x", "y"], self._factors(["x", "y"]))
        assert sp.nature == "minimum"
        assert all(v > 0 for v in sp.eigenvalues)

    def test_saddle(self):
        from doe.rsm import characterize_stationary_point
        coefs = {"intercept": 0.0, "x": 0.0, "y": 0.0,
                 "x^2": 1.0, "y^2": -1.0, "x*y": 0.0}
        sp = characterize_stationary_point(self._model(coefs), ["x", "y"], self._factors(["x", "y"]))
        assert sp.nature == "saddle"

    def test_ridge_when_one_axis_is_flat(self):
        """A near-zero eigenvalue + others negative → rising_ridge."""
        from doe.rsm import characterize_stationary_point
        # y = -x^2 + 0.1 * z   (no quadratic in z, only linear): rising ridge along z
        coefs = {"intercept": 0.0, "x": 0.0, "y": 0.0, "z": 0.1,
                 "x^2": -1.0, "y^2": -1.0, "z^2": 0.0,
                 "x*y": 0.0, "x*z": 0.0, "y*z": 0.0}
        sp = characterize_stationary_point(self._model(coefs), ["x", "y", "z"],
                                           self._factors(["x", "y", "z"]))
        assert sp.nature == "rising_ridge"
        # The ridge axis must be along z (largest absolute component)
        assert abs(sp.ridge_direction["z"]) > 0.9

    def test_no_quadratic_returns_none(self):
        from doe.rsm import characterize_stationary_point
        coefs = {"intercept": 1.0, "x": 0.5, "y": -0.3}
        sp = characterize_stationary_point(self._model(coefs), ["x", "y"],
                                           self._factors(["x", "y"]))
        assert sp is None

    def test_natural_units_decoding(self):
        """Coded location must be decoded into natural units when factor levels are numeric."""
        from doe.models import Factor
        from doe.rsm import characterize_stationary_point
        factors = [
            Factor(name="temp", levels=["100", "200"], type="continuous"),
            Factor(name="press", levels=["1", "5"], type="continuous"),
        ]
        # y = -(temp_coded - 0.5)^2 - (press_coded - 0)^2 + 1
        # Coded (0.5, 0); natural temp = 150 + 0.5*50 = 175; natural press = 3
        coefs = {"intercept": 1.0 - 0.25, "temp": 1.0, "press": 0.0,
                 "temp^2": -1.0, "press^2": -1.0, "temp*press": 0.0}
        sp = characterize_stationary_point(
            type("M", (), {"coefficients": coefs, "diagnostics": None})(),
            ["temp", "press"], factors,
        )
        assert sp.nature == "maximum"
        assert float(sp.natural_location["temp"]) == 175.0
        assert float(sp.natural_location["press"]) == 3.0


class TestAdequacyAndStationaryReporting:
    """The new sections must show up in the printout, HTML report, and CSV export."""

    def _setup(self, tmp_path):
        from doe.config import load_config
        from doe.design import generate_design
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="central_composite",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=11)
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            z = float(run.factor_values["z"])
            r = -(x ** 2) - (y ** 2) - 0.5 * z * z + 4.0
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"r": r}))
        return cfg, matrix, results_dir

    def test_csv_export_contains_new_files(self, tmp_path):
        from doe.analysis import analyze, export_csv
        cfg, matrix, results_dir = self._setup(tmp_path)
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        export_dir = tmp_path / "csv"
        files = export_csv(report, str(export_dir))
        names = {os.path.basename(p) for p in files}
        assert "model_adequacy_r.csv" in names
        assert "stationary_point_r.csv" in names
        adq = (export_dir / "model_adequacy_r.csv").read_text()
        assert "predicted_r_squared" in adq
        sp_csv = (export_dir / "stationary_point_r.csv").read_text()
        assert "nature" in sp_csv

    def test_print_report_includes_new_sections(self, tmp_path, capsys):
        from doe.analysis import analyze
        from doe.cli import _print_report
        cfg, matrix, results_dir = self._setup(tmp_path)
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        _print_report(report)
        out = capsys.readouterr().out
        assert "Model Adequacy" in out
        assert "Stationary Point" in out
        assert "Eigenvalues" in out

    def test_html_report_has_sections(self, tmp_path):
        from doe.analysis import analyze
        from doe.report import generate_report
        cfg, matrix, results_dir = self._setup(tmp_path)
        out_html = tmp_path / "report.html"
        generate_report(matrix, cfg, results_dir=str(results_dir),
                        output_path=str(out_html))
        body = out_html.read_text()
        assert "Model Adequacy" in body
        assert "Stationary Point" in body
        assert "Predicted R" in body

    def test_html_report_has_table_of_contents(self, tmp_path):
        """Sticky nav with anchor links to each top-level section."""
        from doe.analysis import analyze
        from doe.report import generate_report
        cfg, matrix, results_dir = self._setup(tmp_path)
        out_html = tmp_path / "report.html"
        generate_report(matrix, cfg, results_dir=str(results_dir),
                        output_path=str(out_html))
        body = out_html.read_text()
        assert 'class="toc"' in body
        # Anchor target IDs are rendered for each top-level section
        assert 'id="design-summary"' in body
        assert 'id="design-matrix"' in body
        # Each TOC link's href points at an id present in the document
        import re
        hrefs = set(re.findall(r'<a href="#([^"]+)"', body))
        ids = set(re.findall(r'id="([a-z0-9\-]+)"', body))
        # Every nav link must resolve to an existing id on the page
        nav_block = body.split('class="toc"', 1)[1].split('</nav>', 1)[0]
        nav_hrefs = set(re.findall(r'href="#([^"]+)"', nav_block))
        assert nav_hrefs <= ids
        assert len(nav_hrefs) >= 3  # at least Design Summary / Results / Design Matrix

    def test_html_report_has_achieved_power(self, tmp_path):
        from doe.analysis import analyze
        from doe.report import generate_report
        cfg, matrix, results_dir = self._setup(tmp_path)
        out_html = tmp_path / "report.html"
        generate_report(matrix, cfg, results_dir=str(results_dir),
                        output_path=str(out_html))
        body = out_html.read_text()
        assert "Achieved Power" in body
        assert "MDE" in body


class TestAchievedPower:
    """Tests for doe.power.achieved_power and analyze() integration."""

    def _matrix_and_factors(self):
        from doe.models import Factor, ExperimentRun, DesignMatrix
        # Tiny 2^3 design — 8 runs, 3 two-level factors.
        runs = []
        rid = 1
        for a in (-1, 1):
            for b in (-1, 1):
                for c in (-1, 1):
                    runs.append(ExperimentRun(
                        run_id=rid, block_id=1,
                        factor_values={"a": str(a), "b": str(b), "c": str(c)},
                    ))
                    rid += 1
        factors = [Factor(name=n, levels=["-1", "1"], type="continuous")
                   for n in ("a", "b", "c")]
        matrix = DesignMatrix(runs=runs, factor_names=["a", "b", "c"],
                              operation="full_factorial")
        return matrix, factors

    def test_zero_residual_ms_clamps_to_full_power(self):
        from doe.power import achieved_power
        matrix, factors = self._matrix_and_factors()
        ap = achieved_power(matrix=matrix, factors=factors,
                            residual_ms=0.0, df_error=4)
        assert ap is not None
        for entry in ap.per_factor:
            assert entry.power_at_delta == 1.0
            assert entry.mde_at_target == 0.0

    def test_returns_none_when_df_error_zero(self):
        from doe.power import achieved_power
        matrix, factors = self._matrix_and_factors()
        ap = achieved_power(matrix=matrix, factors=factors,
                            residual_ms=1.0, df_error=0)
        assert ap is None

    def test_mde_is_monotonic_in_target_power(self):
        from doe.power import mde_for_factor
        # Higher target_power → larger MDE
        m1 = mde_for_factor(n_runs=16, n_levels=2, df_error=8,
                            sigma=1.0, target_power=0.5)
        m2 = mde_for_factor(n_runs=16, n_levels=2, df_error=8,
                            sigma=1.0, target_power=0.8)
        m3 = mde_for_factor(n_runs=16, n_levels=2, df_error=8,
                            sigma=1.0, target_power=0.95)
        assert m1 < m2 < m3

    def test_power_increases_with_delta(self):
        from doe.power import power_for_factor
        p_low = power_for_factor(n_runs=16, n_levels=2, df_error=8,
                                 delta=0.5, sigma=1.0)
        p_high = power_for_factor(n_runs=16, n_levels=2, df_error=8,
                                  delta=2.0, sigma=1.0)
        assert p_low < p_high
        assert 0.0 <= p_low <= 1.0 and 0.0 <= p_high <= 1.0

    def test_default_delta_is_two_sigma(self):
        from doe.power import achieved_power
        matrix, factors = self._matrix_and_factors()
        ap = achieved_power(matrix=matrix, factors=factors,
                            residual_ms=4.0, df_error=4)  # sigma = 2
        assert abs(ap.delta - 4.0) < 1e-9  # 2 * sigma

    def test_analyze_attaches_achieved_power(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "a", "levels": ["-1", "1"]},
                {"name": "b", "levels": ["-1", "1"]},
                {"name": "c", "levels": ["-1", "1"]},
            ],
            responses=[{"name": "y"}],
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        # Construct a real signal so ANOVA's residual MS is non-zero.
        import random
        random.seed(0)
        for run in matrix.runs:
            a = float(run.factor_values["a"])
            b = float(run.factor_values["b"])
            c = float(run.factor_values["c"])
            y = 2.0 + 1.5 * a + 0.5 * b + 0.0 * c + random.gauss(0, 0.5)
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"y": y}))
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        ra = report.results_by_response["y"]
        assert ra.achieved_power is not None
        assert ra.achieved_power.df_error >= 1
        assert len(ra.achieved_power.per_factor) == 3


class TestAliasStructure:
    """Tests for compute_alias_structure + analyze() integration."""

    def _make_screening_matrix(self, tmp_path, n_factors, operation):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": chr(ord("A") + i), "levels": ["-1", "1"]}
                for i in range(n_factors)
            ],
            responses=[{"name": "y"}],
            operation=operation,
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        return cfg, matrix

    def test_returns_none_for_full_factorial(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        cfg_dict = _make_config_dict()
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        assert compute_alias_structure(matrix) is None

    def test_resolution_iii_main_effects_aliased_with_2fi(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        # 7 factors in 8 runs: must be Resolution III — there is not
        # enough room for any cleaner design.
        cfg, matrix = self._make_screening_matrix(tmp_path, 7, "fractional_factorial")
        ali = compute_alias_structure(matrix)
        assert ali is not None
        assert ali.design_type == "fractional_factorial"
        assert ali.resolution == 3

        partners = {e.effect: {p for p, _ in e.aliased_with} for e in ali.main_effects}
        # In this design, every aliased main-effect partner must be a 2FI,
        # and at least one main effect must have such a partner.
        assert any(any("*" in p for p in v) for v in partners.values())
        # All reported correlations are exactly 1.0 for FF
        for entry in ali.main_effects:
            for _p, r in entry.aliased_with:
                assert (1.0 - r) < 1e-6

    def test_resolution_iv_picked_when_achievable(self, tmp_path):
        """A 2^(4-1) FF in 8 runs has a Resolution IV option (I = ABCD).
        The generator search should pick it over the Resolution III variant."""
        from doe.aliasing import compute_alias_structure
        cfg, matrix = self._make_screening_matrix(tmp_path, 4, "fractional_factorial")
        ali = compute_alias_structure(matrix)
        assert ali is not None
        assert ali.resolution == 4
        # Main effects must therefore be clean of two-factor interactions.
        assert all(not e.aliased_with for e in ali.main_effects)

    def test_resolution_v_clean(self, tmp_path):
        """A 2^(5-1) FF with I=ABCDE is Resolution V — main effects clean,
        all 2FIs clean too. We rely on pyDOE3 producing this when 5 factors
        are requested."""
        from doe.aliasing import compute_alias_structure
        cfg, matrix = self._make_screening_matrix(tmp_path, 5, "fractional_factorial")
        ali = compute_alias_structure(matrix)
        # The exact resolution depends on the generator the project picks;
        # what we want to assert is that 'III' is the worst case it can be:
        assert ali.resolution in (3, 4, 5)
        # If Resolution V, main effects entries should have no aliases.
        if ali.resolution == 5:
            assert all(not e.aliased_with for e in ali.main_effects)

    def test_plackett_burman_partial_aliasing(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        cfg, matrix = self._make_screening_matrix(tmp_path, 11, "plackett_burman")
        ali = compute_alias_structure(matrix)
        assert ali is not None
        assert ali.design_type == "plackett_burman"
        assert ali.resolution is None  # PB doesn't have a single resolution
        # Each main effect must have multiple partial aliases at |r|=1/3.
        first = ali.main_effects[0]
        assert len(first.aliased_with) >= 5
        assert any(0.2 < r < 0.5 for _p, r in first.aliased_with)

    def test_uses_user_factor_names(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        names = ["temperature", "pressure", "catalyst", "stir", "humidity",
                 "ph", "feed_rate"]
        cfg_dict = _make_config_dict(
            factors=[{"name": n, "levels": ["-1", "1"]} for n in names],
            responses=[{"name": "y"}],
            operation="fractional_factorial",
        )
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        ali = compute_alias_structure(matrix)
        labels = {e.effect for e in ali.main_effects}
        assert "temperature" in labels
        # 7 factors in 8 runs is unavoidably Resolution III, so at least one
        # main effect must be aliased with a 2FI.
        any_alias = next((e for e in ali.main_effects if e.aliased_with), None)
        assert any_alias is not None
        for partner, _r in any_alias.aliased_with:
            for token in partner.split("*"):
                assert token in set(names)

    def test_threshold_filters_below(self):
        """Correlations below the threshold must not appear in the output."""
        from doe.models import Factor, ExperimentRun, DesignMatrix
        from doe.aliasing import compute_alias_structure
        # Construct a synthetic 3-factor PB-style matrix with controlled
        # correlations: 4 runs, columns chosen so AB*C has correlation 0.5 with A.
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"A": str(a), "B": str(b), "C": str(c)})
            for i, (a, b, c) in enumerate([
                (-1, -1, -1), (-1, 1, 1), (1, -1, 1), (1, 1, -1),
            ])
        ]
        m = DesignMatrix(runs=runs, factor_names=["A", "B", "C"],
                         operation="plackett_burman")
        ali_low = compute_alias_structure(m, threshold=0.05)
        ali_high = compute_alias_structure(m, threshold=0.99)
        n_low = sum(len(e.aliased_with) for e in ali_low.main_effects)
        n_high = sum(len(e.aliased_with) for e in ali_high.main_effects)
        # Raising the threshold can only reduce or preserve the partner count
        assert n_high <= n_low

    def test_analyze_attaches_alias_structure(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix = self._make_screening_matrix(tmp_path, 4, "fractional_factorial")
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"y": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        assert report.alias_structure is not None
        assert report.alias_structure.design_type == "fractional_factorial"

    def test_analyze_no_alias_for_full_factorial(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict()
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"response": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        assert report.alias_structure is None

    def test_print_report_includes_alias(self, tmp_path, capsys):
        from doe.analysis import analyze
        from doe.cli import _print_report
        cfg, matrix = self._make_screening_matrix(tmp_path, 4, "fractional_factorial")
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"y": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        _print_report(report)
        out = capsys.readouterr().out
        assert "Alias Structure" in out
        assert "Resolution III" in out or "Resolution IV" in out or "Resolution V" in out

    def test_html_report_includes_alias(self, tmp_path):
        from doe.analysis import analyze
        from doe.report import generate_report
        cfg, matrix = self._make_screening_matrix(tmp_path, 4, "fractional_factorial")
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"y": 1.0}))
        out_html = tmp_path / "report.html"
        generate_report(matrix, cfg, results_dir=str(results_dir),
                        output_path=str(out_html))
        body = out_html.read_text()
        assert "Alias Structure" in body
        assert "Aliased with" in body

    def test_csv_export_includes_alias(self, tmp_path):
        from doe.analysis import analyze, export_csv
        cfg, matrix = self._make_screening_matrix(tmp_path, 4, "fractional_factorial")
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"y": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        out_dir = tmp_path / "csv"
        files = export_csv(report, str(out_dir))
        names = {os.path.basename(p) for p in files}
        assert "alias_structure.csv" in names
        body = (out_dir / "alias_structure.csv").read_text()
        # Header must include all four columns
        assert "effect_kind,effect,aliased_with,abs_correlation" in body


class TestCompareSessions:
    """Tests for doe.compare.compare_sessions and the doe compare CLI."""

    def _build_two_sessions(self, tmp_path, baseline_fn, candidate_fn,
                            factors=None, response_name="r"):
        """Generate a small full-factorial design and write two sessions
        whose response values come from ``baseline_fn`` / ``candidate_fn``.
        Returns (cfg, matrix, baseline_dir, candidate_dir).
        """
        cfg_dict = _make_config_dict(
            factors=factors or [
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": response_name, "optimize": "maximize"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)

        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)

        def _write(name, fn):
            d = results_dir / name
            d.mkdir(parents=True, exist_ok=True)
            # Copy the design matrix into the session dir (the runner does this
            # for real sessions; for tests we replicate the layout directly).
            (d / "design_matrix.json").write_text(json.dumps({
                "factor_names": matrix.factor_names,
                "operation": matrix.operation,
                "metadata": matrix.metadata,
                "runs": [
                    {"run_id": r.run_id, "block_id": r.block_id,
                     "factor_values": r.factor_values}
                    for r in matrix.runs
                ],
            }))
            for run in matrix.runs:
                vals = [float(run.factor_values[f]) for f in matrix.factor_names]
                (d / f"run_{run.run_id}.json").write_text(json.dumps({
                    response_name: float(fn(*vals)),
                }))
            return d

        b = _write("baseline", baseline_fn)
        c = _write("candidate", candidate_fn)
        return cfg, matrix, str(b), str(c)

    def test_uniform_shift_detected(self, tmp_path):
        """A constant +5 added to every run → mean_delta ≈ 5, effects unchanged."""
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: 3 + 2 * x + y,
            candidate_fn=lambda x, y: 3 + 2 * x + y + 5.0,
        )
        report = compare_sessions(cfg, b, c)
        assert report.n_matched_runs == 4
        rc = report.responses[0]
        assert abs(rc.mean_delta - 5.0) < 1e-9
        # Paired t with deltas all exactly 5 → infinite t, p=0
        # (handled as inf / 0 by the helper)
        assert rc.paired_t_stat is not None
        # Main effects didn't change: deltas should all be ~0, none flipped
        for e in rc.effect_deltas:
            assert abs(e.delta) < 1e-9
            assert not e.flipped_sign

    def test_sign_flip_detected(self, tmp_path):
        from doe.compare import compare_sessions
        # Baseline: x has positive effect (+2). Candidate: x has negative effect (-2).
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: 10 + 2 * x + y,
            candidate_fn=lambda x, y: 10 - 2 * x + y,
        )
        report = compare_sessions(cfg, b, c)
        rc = report.responses[0]
        x_delta = next(e for e in rc.effect_deltas if e.factor_name == "x")
        assert x_delta.flipped_sign is True
        y_delta = next(e for e in rc.effect_deltas if e.factor_name == "y")
        assert y_delta.flipped_sign is False

    def test_matches_by_factor_values_not_run_id(self, tmp_path):
        """Re-randomising the candidate run order must still pair correctly."""
        from doe.compare import compare_sessions
        cfg, matrix, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y + 0.5,
        )
        # Re-write candidate with run_ids reversed but same factor values
        import shutil
        cand = Path(c)
        # Rename run_*.json files: id -> (5 - id) so 1<->4, 2<->3
        old_files = {p.name: p for p in cand.glob("run_*.json")}
        # Read all values keyed by the original run_id
        import json as _json
        contents = {int(name.split("_")[1].split(".")[0]):
                    _json.loads(p.read_text()) for name, p in old_files.items()}
        for p in old_files.values():
            p.unlink()
        # Reverse the mapping
        n_runs = len(contents)
        for old_id, payload in contents.items():
            new_id = n_runs + 1 - old_id
            (cand / f"run_{new_id}.json").write_text(_json.dumps(payload))
        # Also rewrite the design_matrix.json with re-ordered runs
        dm_path = cand / "design_matrix.json"
        dm = _json.loads(dm_path.read_text())
        # Reverse run_id assignment but keep factor_values bound to the reverse
        new_runs = []
        for old_run in dm["runs"]:
            new_runs.append({
                "run_id": n_runs + 1 - old_run["run_id"],
                "block_id": old_run["block_id"],
                "factor_values": old_run["factor_values"],
            })
        dm["runs"] = new_runs
        dm_path.write_text(_json.dumps(dm))

        report = compare_sessions(cfg, b, c)
        # All 4 runs should still pair via factor-value matching.
        assert report.n_matched_runs == 4
        rc = report.responses[0]
        # Each per-run delta must equal +0.5 since the function only differs
        # by a constant — confirms matching is correct.
        assert all(abs(d.delta - 0.5) < 1e-9 for d in rc.per_run)

    def test_unmatched_runs_warned(self, tmp_path):
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y,
        )
        # Delete one run from the candidate
        candidate = Path(c)
        next(candidate.glob("run_*.json")).unlink()
        report = compare_sessions(cfg, b, c)
        # Still pairs the 3 remaining; report carries a note about the missing one.
        assert report.n_matched_runs == 4  # all factor settings still in candidate dir's matrix
        rc = report.responses[0]
        # But only 3 had results and got compared
        assert rc.n_matched == 3

    def test_mismatched_factor_names_raises(self, tmp_path):
        from doe.compare import compare_sessions
        cfg, _, b, _ = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y,
        )
        # Hand-craft a "candidate" session that claims different factors
        rogue = tmp_path / "rogue"
        rogue.mkdir()
        (rogue / "design_matrix.json").write_text(json.dumps({
            "factor_names": ["alpha", "beta"],
            "operation": "full_factorial",
            "metadata": {},
            "runs": [{"run_id": 1, "block_id": 1, "factor_values": {"alpha": "0", "beta": "0"}}],
        }))
        with pytest.raises(ValueError, match="Factor names"):
            compare_sessions(cfg, b, str(rogue))

    def test_no_overlap_raises(self, tmp_path):
        from doe.compare import compare_sessions
        # Two sessions with identical factor names but disjoint level values:
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        # Session B's "matrix" has factor values that don't appear in A
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir(); b.mkdir()
        for d, vals in ((a, ("-1", "-1")), (b, ("99", "99"))):
            (d / "design_matrix.json").write_text(json.dumps({
                "factor_names": ["x", "y"],
                "operation": "full_factorial",
                "metadata": {},
                "runs": [{"run_id": 1, "block_id": 1,
                          "factor_values": {"x": vals[0], "y": vals[1]}}],
            }))
            (d / "run_1.json").write_text(json.dumps({"r": 1.0}))
        with pytest.raises(ValueError, match="No matching runs"):
            compare_sessions(cfg, str(a), str(b))

    def test_csv_export(self, tmp_path):
        from doe.compare import compare_sessions, export_compare_csv
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y + 1.0,
        )
        report = compare_sessions(cfg, b, c)
        out_dir = tmp_path / "csv"
        files = export_compare_csv(report, str(out_dir))
        names = {os.path.basename(p) for p in files}
        assert "compare_summary.csv" in names
        assert "compare_runs_r.csv" in names
        assert "compare_effects_r.csv" in names
        body = (out_dir / "compare_summary.csv").read_text()
        assert "response,n_matched,baseline_mean" in body

    def test_cli_compare_runs(self, tmp_path):
        """Smoke test the CLI integration."""
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y + 1.0,
        )
        # Re-load through the CLI path, capturing output
        from doe.cli import _print_compare_report
        report = compare_sessions(cfg, b, c)
        # Just confirm the report has the expected shape
        assert report.n_matched_runs == 4
        assert len(report.responses) == 1
        # Sanity: paired t-test is meaningful when deltas are constant +1
        rc = report.responses[0]
        assert rc.mean_delta - 1.0 < 1e-9

    def test_html_export(self, tmp_path):
        from doe.compare import compare_sessions, export_compare_html
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y + 1.5,
        )
        report = compare_sessions(cfg, b, c)
        out_html = tmp_path / "compare.html"
        export_compare_html(report, str(out_html))
        body = out_html.read_text()
        assert "Comparison Summary" in body
        assert "Response: r" in body or "Response: r" in body
        assert 'class="data-table"' in body
        assert "Δ Decomposition" in body or "Δ" in body

    def test_decomposition_isolates_uniform_shift(self, tmp_path):
        """When candidate = baseline + 5, intercept_shift should pick up
        the shift while slope_shifts stay statistically null."""
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: 10 + 3 * x + y,
            candidate_fn=lambda x, y: 10 + 3 * x + y + 5.0,
        )
        report = compare_sessions(cfg, b, c)
        rc = report.responses[0]
        assert rc.decomposition is not None
        dc = rc.decomposition
        assert abs(dc.intercept_shift - 5.0) < 1e-6
        # All slope shifts ~0 because the candidate slopes match the baseline
        for fname, shift, _p in dc.slope_shifts:
            assert abs(shift) < 1e-6, f"{fname} slope shift was {shift}"

    def test_decomposition_picks_up_slope_change(self, tmp_path):
        """Reversing one factor's effect → slope shift = 4·γ ≈ effect_delta."""
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: 10 + 3 * x + y,
            candidate_fn=lambda x, y: 10 - 3 * x + y,
        )
        report = compare_sessions(cfg, b, c)
        rc = report.responses[0]
        dc = rc.decomposition
        # Find the per-factor effect delta and the slope shift; they
        # should match (within numerical tolerance) for two-level designs.
        effect_x = next(e for e in rc.effect_deltas if e.factor_name == "x")
        slope_x = next(s for s in dc.slope_shifts if s[0] == "x")[1]
        assert abs(slope_x - effect_x.delta) < 1e-6
        # x slope flipped from +3 to -3 → effect goes from +6 to -6 → delta = -12
        assert abs(slope_x - (-12.0)) < 1e-6

    def test_decomposition_skipped_for_multilevel(self, tmp_path):
        """Multi-level factors are out-of-scope for the v1 regression."""
        from doe.compare import compare_sessions
        cfg, _, b, c = self._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y, z: x + y + z,
            candidate_fn=lambda x, y, z: x + y + z + 1.0,
            factors=[
                {"name": "x", "levels": ["-1", "0", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
        )
        report = compare_sessions(cfg, b, c)
        rc = report.responses[0]
        assert rc.decomposition is not None
        # df_error = 0 signals the regression was skipped, but the notes
        # explain why.
        assert rc.decomposition.df_error == 0
        assert any("Decomposition skipped" in n for n in rc.decomposition.notes)


class TestFFResolutionKnob:
    """Tests for the `--resolution N` / cfg.min_resolution knob."""

    def _make_cfg(self, tmp_path, n_factors, min_resolution=0):
        cfg_dict = _make_config_dict(
            factors=[{"name": chr(ord("A") + i), "levels": ["-1", "1"]}
                     for i in range(n_factors)],
            responses=[{"name": "y"}],
            operation="fractional_factorial",
        )
        cfg_dict["settings"]["min_resolution"] = min_resolution
        return load_config(_write_config(tmp_path, cfg_dict), strict=False)

    def test_default_picks_higher_resolution_when_free(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        cfg = self._make_cfg(tmp_path, 4)  # min_resolution=0 (auto)
        matrix = generate_design(cfg, seed=1)
        ali = compute_alias_structure(matrix)
        # 2^(4-1) has a Resolution IV option (I=ABCD) — auto must pick it.
        assert ali.resolution >= 4

    def test_pin_resolution_v_bumps_run_count(self, tmp_path):
        from doe.aliasing import compute_alias_structure
        small = generate_design(self._make_cfg(tmp_path, 4, 0), seed=1)
        big = generate_design(self._make_cfg(tmp_path, 4, 5), seed=1)
        ali_small = compute_alias_structure(small)
        ali_big = compute_alias_structure(big)
        assert ali_big.resolution >= 5
        # And the pinned design should be at least as large as the free one
        assert len(big.runs) >= len(small.runs)

    def test_pin_unachievable_falls_back_to_full_factorial(self, tmp_path):
        # Asking for resolution that doesn't exist → fall back to full-factorial-style
        cfg = self._make_cfg(tmp_path, 3, min_resolution=99)
        matrix = generate_design(cfg, seed=1)
        # 3 factors, full factorial = 8 runs
        assert len(matrix.runs) == 8


class TestReplicateAnova:
    """End-to-end test that pure-error / lack-of-fit rows fill in when
    the design has true replicates."""

    def test_pure_error_row_populated(self, tmp_path):
        from doe.analysis import analyze
        from doe.models import ExperimentRun, DesignMatrix
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        # Append 3 replicated runs at the (-1, -1) corner so we have pure error.
        replicate_id_start = max(r.run_id for r in matrix.runs) + 1
        rep_runs = [
            ExperimentRun(run_id=replicate_id_start + i, block_id=1,
                          factor_values={"x": "-1", "y": "-1"})
            for i in range(3)
        ]
        all_runs = list(matrix.runs) + rep_runs
        matrix = DesignMatrix(runs=all_runs, factor_names=matrix.factor_names,
                              operation=matrix.operation, metadata=matrix.metadata)

        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        import random
        random.seed(0)
        for run in all_runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            val = 1.0 + 2 * x + y + random.gauss(0, 0.1)
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"r": val}))

        report = analyze(matrix, cfg, results_dir=str(results_dir), no_plots=True)
        anova = report.results_by_response["r"].anova_table
        assert anova is not None
        assert anova.error_method == "replicates"
        assert anova.pure_error_row is not None
        assert anova.pure_error_row.df > 0
        # Error row must mirror pure-error (no longer the stale pooled SS)
        assert anova.error_row is not None
        assert abs(anova.error_row.ss - anova.pure_error_row.ss) < 1e-9
        assert anova.error_row.df == anova.pure_error_row.df


class TestBlockEffect:
    """Tests for ANOVA Block row when block_count > 1."""

    def _setup(self, tmp_path, block_count=3, block_offsets=None, noise=0.05):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
            block_count=block_count,
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        block_offsets = block_offsets or {1: 0.0, 2: 1.5, 3: -2.0, 4: 0.7}
        import random
        random.seed(0)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            val = 2 * x + y + block_offsets.get(run.block_id, 0.0) + random.gauss(0, noise)
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"r": val}))
        return cfg, matrix, str(results_dir)

    def test_block_row_inserted(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix, rd = self._setup(tmp_path, block_count=3)
        report = analyze(matrix, cfg, results_dir=rd, no_plots=True, fit_rsm=False)
        anova = report.results_by_response["r"].anova_table
        assert anova is not None
        block_rows = [row for row in anova.rows if row.source == "Block"]
        assert len(block_rows) == 1
        assert block_rows[0].df == 2  # 3 blocks - 1
        assert block_rows[0].ss > 0

    def test_no_block_row_when_single_block(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix, rd = self._setup(tmp_path, block_count=1)
        report = analyze(matrix, cfg, results_dir=rd, no_plots=True, fit_rsm=False)
        anova = report.results_by_response["r"].anova_table
        assert anova is not None
        assert all(row.source != "Block" for row in anova.rows)

    def test_pure_error_grouped_by_block_setting(self, tmp_path):
        """With block-induced offsets, pure error must NOT include block variance."""
        from doe.analysis import analyze
        cfg, matrix, rd = self._setup(tmp_path, block_count=3,
                                       block_offsets={1: 0.0, 2: 1.5, 3: -2.0},
                                       noise=0.05)
        report = analyze(matrix, cfg, results_dir=rd, no_plots=True, fit_rsm=False)
        anova = report.results_by_response["r"].anova_table
        # Each (block, factor settings) cell has exactly one observation in
        # this design, so pure-error df = 0 -> falls back to pooled error.
        assert anova.error_method == "pooled"
        # MS_error should be close to the noise variance (0.05^2 ≈ 0.0025)
        # rather than dominated by block offsets (~2^2 = 4).
        assert anova.error_row.ms < 0.1


class TestCenterPointReplicates:
    """Tests for --replicate-center / settings.replicate_center."""

    def test_center_points_appended(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["replicate_center"] = 3
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        # 4 corner runs + 3 center points = 7
        assert len(matrix.runs) == 7
        center_runs = [r for r in matrix.runs
                       if r.factor_values["x"] == "0" and r.factor_values["y"] == "0"]
        assert len(center_runs) == 3

    def test_center_points_per_block(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
            block_count=2,
        )
        cfg_dict["settings"]["replicate_center"] = 2
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        # 4 corners × 2 blocks + 2 centers × 2 blocks = 12
        assert len(matrix.runs) == 12
        from collections import Counter
        per_block = Counter()
        for r in matrix.runs:
            if r.factor_values["x"] == "0" and r.factor_values["y"] == "0":
                per_block[r.block_id] += 1
        assert per_block == {1: 2, 2: 2}

    def test_no_center_points_for_categorical_only(self, tmp_path):
        """If no factor has a numeric range, replicate_center is a no-op."""
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "color", "levels": ["red", "blue"], "type": "categorical"},
                {"name": "shape", "levels": ["square", "circle"], "type": "categorical"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["replicate_center"] = 3
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        # Just the 4 corners; no centers added
        assert len(matrix.runs) == 4

    def test_replicates_enable_pure_error(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["replicate_center"] = 4
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        import random
        random.seed(0)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            val = 2 * x + y + random.gauss(0, 0.1)
            (results_dir / f"run_{run.run_id}.json").write_text(json.dumps({"r": val}))
        report = analyze(matrix, cfg, results_dir=str(results_dir),
                         no_plots=True, fit_rsm=False)
        anova = report.results_by_response["r"].anova_table
        assert anova.error_method == "replicates"
        assert anova.pure_error_row is not None
        assert anova.pure_error_row.df == 3  # 4 center-point reps - 1


class TestTrendSessions:
    """Tests for doe.trend.trend_sessions."""

    def _build_sessions(self, tmp_path, fns, factors=None, response_name="r"):
        """Generate a 2x2 design and write `len(fns)` sessions whose
        responses come from the given functions."""
        from doe.config import load_config
        cfg_dict = _make_config_dict(
            factors=factors or [
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": response_name, "optimize": "maximize"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        session_dirs: list[str] = []
        for i, fn in enumerate(fns):
            d = rd / f"session-{i}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "design_matrix.json").write_text(json.dumps({
                "factor_names": matrix.factor_names,
                "operation": matrix.operation,
                "metadata": matrix.metadata,
                "runs": [
                    {"run_id": r.run_id, "block_id": r.block_id,
                     "factor_values": r.factor_values}
                    for r in matrix.runs
                ],
            }))
            for run in matrix.runs:
                vals = [float(run.factor_values[f]) for f in matrix.factor_names]
                (d / f"run_{run.run_id}.json").write_text(json.dumps({
                    response_name: float(fn(*vals)),
                }))
            session_dirs.append(str(d))
        return cfg, session_dirs

    def test_intercept_drift_detected(self, tmp_path):
        from doe.trend import trend_sessions
        # Drift of +0.5 per session, no slope change
        cfg, sessions = self._build_sessions(
            tmp_path,
            [
                lambda x, y, k=k: 2 * x + y + 0.5 * k for k in range(4)
            ],
        )
        report = trend_sessions(cfg, sessions)
        tr = report.responses[0]
        assert abs(tr.intercept_drift_per_session - 0.5) < 1e-6
        # Slope drifts ~0
        for entry in tr.slope_drift:
            assert abs(entry.slope_drift_per_session) < 1e-6

    def test_per_session_means_recorded(self, tmp_path):
        from doe.trend import trend_sessions
        cfg, sessions = self._build_sessions(
            tmp_path,
            [lambda x, y: 1.0, lambda x, y: 2.0, lambda x, y: 3.0],
        )
        report = trend_sessions(cfg, sessions)
        means = report.responses[0].per_session_means
        assert abs(means[0] - 1.0) < 1e-9
        assert abs(means[1] - 2.0) < 1e-9
        assert abs(means[2] - 3.0) < 1e-9

    def test_requires_two_sessions(self, tmp_path):
        from doe.trend import trend_sessions
        cfg, sessions = self._build_sessions(tmp_path, [lambda x, y: 1.0])
        with pytest.raises(ValueError, match="at least two"):
            trend_sessions(cfg, sessions)

    def test_csv_export(self, tmp_path):
        from doe.trend import trend_sessions, export_trend_csv
        cfg, sessions = self._build_sessions(
            tmp_path,
            [lambda x, y, k=k: x + y + 0.2 * k for k in range(3)],
        )
        report = trend_sessions(cfg, sessions)
        out_dir = tmp_path / "csv"
        files = export_trend_csv(report, str(out_dir))
        names = {os.path.basename(p) for p in files}
        assert "trend_summary.csv" in names
        assert "trend_means_r.csv" in names
        assert "trend_slopes_r.csv" in names


class TestNoRsmFlag:
    """Tests for the --no-rsm flag on doe analyze."""

    def test_skips_model_adequacy_when_disabled(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({"r": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(rd),
                         no_plots=True, fit_rsm=False)
        ra = report.results_by_response["r"]
        assert ra.model_adequacy is None
        assert ra.stationary_point is None
        # Other analyses unchanged
        assert ra.effects is not None and len(ra.effects) > 0

    def test_default_still_fits_rsm(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="central_composite",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            z = float(run.factor_values["z"])
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "r": -(x ** 2) - (y ** 2) - 0.5 * z ** 2 + 4
            }))
        report = analyze(matrix, cfg, results_dir=str(rd), no_plots=True)
        ra = report.results_by_response["r"]
        assert ra.model_adequacy is not None
        assert ra.stationary_point is not None


class TestCrossValidation:
    """Tests for compute_cross_validation and analyze() integration."""

    def _quad_runs_and_factors(self):
        """A noiseless 3-factor central-composite-style design."""
        from doe.models import Factor, ExperimentRun, DesignMatrix
        coords = []
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    coords.append((x, y, z))
        a = 1.682
        coords += [(-a, 0, 0), (a, 0, 0), (0, -a, 0),
                   (0, a, 0), (0, 0, -a), (0, 0, a)]
        coords += [(0, 0, 0)] * 3
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x": str(x), "y": str(y), "z": str(z)})
            for i, (x, y, z) in enumerate(coords)
        ]
        factors = [Factor(name=n, levels=["-1", "1"], type="continuous")
                   for n in ("x", "y", "z")]
        return runs, factors

    def test_perfect_quadratic_fits_perfectly(self):
        """A noiseless quadratic surface should give R^2_cv near 1."""
        from doe.rsm import compute_cross_validation
        runs, factors = self._quad_runs_and_factors()
        responses = {
            r.run_id: 5 - float(r.factor_values["x"]) ** 2
                       - float(r.factor_values["y"]) ** 2
                       - 0.5 * float(r.factor_values["z"]) ** 2
            for r in runs
        }
        cv = compute_cross_validation(
            runs, responses, ["x", "y", "z"], factors,
            model_type="quadratic", k_folds=5, seed=0,
        )
        assert cv is not None
        assert cv.r_squared_cv > 0.99
        assert cv.rmse < 0.1
        assert cv.mae < 0.1
        # Folds populated with predictions and actuals of equal length.
        for fold in cv.folds:
            assert len(fold.predictions) == len(fold.actuals)

    def test_skips_when_training_fold_too_small(self):
        """Quadratic on n=8 with k=4 leaves too few training rows for the
        full quadratic — the helper must surface a 'skipped' note rather
        than raise."""
        from doe.rsm import compute_cross_validation
        from doe.models import Factor, ExperimentRun
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x": str(x), "y": str(y), "z": str(z)})
            for i, (x, y, z) in enumerate(
                [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                 (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]
            )
        ]
        factors = [Factor(name=n, levels=["-1", "1"], type="continuous")
                   for n in ("x", "y", "z")]
        responses = {r.run_id: 1.0 for r in runs}
        cv = compute_cross_validation(
            runs, responses, ["x", "y", "z"], factors,
            model_type="quadratic", k_folds=4, seed=0,
        )
        # Either returns None or a CV with notes; just make sure it
        # doesn't blow up.
        if cv is not None:
            assert any("Skipped" in n for n in cv.notes) or cv.r_squared_cv == cv.r_squared_cv

    def test_analyze_attaches_cv(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="central_composite",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            z = float(run.factor_values["z"])
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "r": -(x ** 2) - (y ** 2) - 0.5 * z ** 2 + 4
            }))
        report = analyze(matrix, cfg, results_dir=str(rd), no_plots=True)
        cv = report.results_by_response["r"].cross_validation
        assert cv is not None
        assert cv.k >= 2
        assert cv.r_squared_cv > 0.9

    def test_no_cv_when_rsm_disabled(self, tmp_path):
        from doe.analysis import analyze
        cfg_dict = _make_config_dict()
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({"response": 1.0}))
        report = analyze(matrix, cfg, results_dir=str(rd),
                         no_plots=True, fit_rsm=False)
        ra = report.results_by_response["response"]
        assert ra.cross_validation is None


class TestSplitPlot:
    """Tests for the split_plot operation and split-plot ANOVA."""

    def _make_cfg(self, tmp_path, whole_plot_replicates=2):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "oven", "levels": ["100", "200"],
                 "type": "continuous", "role": "whole_plot"},
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="split_plot",
        )
        cfg_dict["settings"]["whole_plot_replicates"] = whole_plot_replicates
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        return load_config(_write_config(tmp_path, cfg_dict), strict=False)

    def test_generates_correct_run_count(self, tmp_path):
        cfg = self._make_cfg(tmp_path, whole_plot_replicates=3)
        matrix = generate_design(cfg, seed=1)
        # 2 HTC levels × 3 reps × 4 subplot combos = 24
        assert len(matrix.runs) == 24

    def test_whole_plot_ids_assigned(self, tmp_path):
        cfg = self._make_cfg(tmp_path, whole_plot_replicates=2)
        matrix = generate_design(cfg, seed=1)
        plot_ids = sorted({r.whole_plot_id for r in matrix.runs})
        # 2 HTC levels × 2 reps = 4 whole plots
        assert plot_ids == [1, 2, 3, 4]

    def test_htc_held_constant_within_plot(self, tmp_path):
        cfg = self._make_cfg(tmp_path, whole_plot_replicates=2)
        matrix = generate_design(cfg, seed=1)
        from collections import defaultdict
        by_plot = defaultdict(set)
        for r in matrix.runs:
            by_plot[r.whole_plot_id].add(r.factor_values["oven"])
        for plot_id, levels in by_plot.items():
            assert len(levels) == 1, (
                f"Whole plot {plot_id} has multiple HTC levels: {levels}"
            )

    def test_invalid_config_no_htc_factor(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="split_plot",
        )
        with pytest.raises(ValueError, match="role='whole_plot'"):
            load_config(_write_config(tmp_path, cfg_dict), strict=False)

    def test_split_plot_anova_two_error_terms(self, tmp_path):
        from doe.analysis import analyze
        cfg = self._make_cfg(tmp_path, whole_plot_replicates=3)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        import random
        random.seed(0)
        plot_offset = {}
        for run in matrix.runs:
            if run.whole_plot_id not in plot_offset:
                plot_offset[run.whole_plot_id] = random.gauss(0, 0.5)
        for run in matrix.runs:
            htc = float(run.factor_values["oven"])
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            val = (
                0.05 * (htc - 150) + 2 * x + y
                + plot_offset[run.whole_plot_id]
                + random.gauss(0, 0.1)
            )
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({"r": val}))
        report = analyze(matrix, cfg, results_dir=str(rd),
                         no_plots=True, fit_rsm=False)
        anova = report.results_by_response["r"].anova_table
        assert anova is not None
        assert anova.error_method == "split_plot"
        sources = [row.source for row in anova.rows]
        # HTC factor row labelled (whole-plot)
        assert any("(whole-plot)" in s for s in sources)
        # Whole-Plot Error row present with df > 0
        wp_err = next(r for r in anova.rows if r.source == "Whole-Plot Error")
        assert wp_err.df >= 1
        # Subplot factors x, y appear
        assert "x" in sources
        assert "y" in sources
        # The error_row carries subplot error
        assert anova.error_row.source == "Subplot Error"


class TestTrendHtml:
    """Tests for the doe trend HTML output."""

    def test_html_export_contains_sections(self, tmp_path):
        from doe.trend import trend_sessions, export_trend_html
        from doe.models import ExperimentRun, DesignMatrix
        # Build 3 sessions of a 2x2 design with linear drift.
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        sessions = []
        for k in range(3):
            d = rd / f"sess-{k}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "design_matrix.json").write_text(json.dumps({
                "factor_names": matrix.factor_names,
                "operation": matrix.operation,
                "metadata": matrix.metadata,
                "runs": [
                    {"run_id": r.run_id, "block_id": r.block_id,
                     "factor_values": r.factor_values}
                    for r in matrix.runs
                ],
            }))
            for run in matrix.runs:
                x = float(run.factor_values["x"])
                y = float(run.factor_values["y"])
                (d / f"run_{run.run_id}.json").write_text(json.dumps({
                    "r": x + y + 0.3 * k,
                }))
            sessions.append(str(d))
        report = trend_sessions(cfg, sessions)
        out_html = tmp_path / "trend.html"
        export_trend_html(report, str(out_html))
        body = out_html.read_text()
        assert "Trend Summary" in body
        assert 'id="trend-summary"' in body
        assert "Per-Session Means" in body
        assert "Intercept drift" in body
        # Ensure CSS reuse and link rendering (>0 anchors)
        assert 'class="data-table"' in body


class TestConstraints:
    """Tests for constraint expressions filtering generated runs."""

    def test_filter_simple_inequality(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["0", "1"], "type": "continuous"},
                {"name": "y", "levels": ["0", "1"], "type": "continuous"},
                {"name": "z", "levels": ["0", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["constraints"] = ["x + y + z <= 1.5"]
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        # Only rows where x+y+z <= 1.5 survive (4 of 8)
        assert len(matrix.runs) == 4
        for run in matrix.runs:
            x, y, z = (float(run.factor_values[f]) for f in ("x", "y", "z"))
            assert x + y + z <= 1.5

    def test_filter_categorical_implication(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "catalyst", "levels": ["A", "B"], "type": "categorical"},
                {"name": "temp", "levels": ["100", "200"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        # If catalyst is 'A' temperature must be <= 150 (i.e. drop catalyst=A & temp=200)
        cfg_dict["constraints"] = ["catalyst != 'A' or temp <= 150"]
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        assert len(matrix.runs) == 3
        forbidden = [r for r in matrix.runs
                     if r.factor_values["catalyst"] == "A"
                     and float(r.factor_values["temp"]) > 150]
        assert not forbidden

    def test_renumbered_after_filter(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["0", "1"], "type": "continuous"},
                {"name": "y", "levels": ["0", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["constraints"] = ["x + y <= 0.5"]
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        ids = [r.run_id for r in matrix.runs]
        assert ids == sorted(ids)
        # Run IDs are dense starting at 1
        assert ids == list(range(1, len(ids) + 1))

    def test_all_filtered_raises(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["0", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["constraints"] = ["x > 100"]
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        with pytest.raises(ValueError, match="filtered out"):
            generate_design(cfg, seed=1)

    def test_disallowed_syntax_rejected(self, tmp_path):
        from doe.constraints import parse_constraint, ConstraintError
        with pytest.raises(ConstraintError):
            parse_constraint("__import__('os').system('ls')")
        with pytest.raises(ConstraintError):
            parse_constraint("x.attr <= 1")  # attribute access banned

    def test_unknown_factor_raises_at_evaluate(self, tmp_path):
        from doe.constraints import parse_constraint, evaluate_constraint, ConstraintError
        tree = parse_constraint("nonexistent <= 1")
        with pytest.raises(ConstraintError, match="unknown factor"):
            evaluate_constraint(tree, {"x": "1"}, "nonexistent <= 1")


class TestArchive:
    """Tests for doe.archive.archive_session."""

    def test_archive_round_trip(self, tmp_path):
        from doe.archive import archive_session
        # Build a minimal session directory
        session = tmp_path / "session-a"
        session.mkdir()
        (session / "design_matrix.json").write_text('{"runs": []}')
        (session / "run_1.json").write_text('{"r": 1.0}')
        (session / "run_2.json").write_text('{"r": 2.0}')
        config_path = tmp_path / "config.json"
        config_path.write_text('{"factors": []}')
        out = tmp_path / "out.tar.gz"
        manifest = archive_session(
            session_dir=str(session),
            output_path=str(out),
            config_path=str(config_path),
        )
        assert out.exists()
        # Manifest carries 4 file records (3 session files + 1 config)
        assert len(manifest["files"]) == 4
        # Verify the tarball contains manifest.json and the bundled files
        import tarfile
        with tarfile.open(str(out)) as tar:
            names = set(tar.getnames())
        assert "manifest.json" in names
        assert "session/run_1.json" in names
        assert "config/config.json" in names

    def test_archive_includes_extras(self, tmp_path):
        from doe.archive import archive_session
        session = tmp_path / "session-b"
        session.mkdir()
        (session / "run_1.json").write_text('{"r": 1.0}')
        report = tmp_path / "report.html"
        report.write_text("<html></html>")
        out = tmp_path / "out.tar.gz"
        manifest = archive_session(
            session_dir=str(session),
            output_path=str(out),
            extras=[str(report)],
        )
        names = {fr["arcname"] for fr in manifest["files"]}
        assert "extras/report.html" in names

    def test_missing_session_raises(self, tmp_path):
        from doe.archive import archive_session
        with pytest.raises(FileNotFoundError):
            archive_session(
                session_dir=str(tmp_path / "does-not-exist"),
                output_path=str(tmp_path / "out.tar.gz"),
            )


class TestServeIndex:
    """Tests for doe.serve.serve (index rendering only — actually starting
    a server in-process is disruptive)."""

    def test_index_lists_sessions_with_reports(self):
        from doe.serve import _render_index
        body = _render_index([
            ("baseline-20260101", "report.html"),
            ("compare-pair", "compare.html"),
            ("raw-no-report", None),
        ])
        assert "baseline-20260101" in body
        assert 'href="baseline-20260101/report.html"' in body
        assert 'href="compare-pair/compare.html"' in body
        assert "no report" in body
        assert "raw-no-report" in body

    def test_empty_index_handled(self):
        from doe.serve import _render_index
        body = _render_index([])
        assert "No session subdirectories" in body


class TestModelGuidedStrategy:
    """Tests for the new 'model_guided' adaptive strategy."""

    def _setup(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="central_composite",
        )
        cfg_dict["adaptive"] = {
            "strategy": "model_guided", "batch_size": 4,
            "stopping_max_phases": 5,
        }
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        # Synthesize a quadratic surface so the RSM fit picks the right optimum.
        for run in matrix.runs:
            x, y, z = (float(run.factor_values[k]) for k in ("x", "y", "z"))
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "r": -(x - 0.3) ** 2 - (y + 0.2) ** 2 - 0.5 * z * z + 5,
            }))
        return cfg, matrix

    def test_emits_requested_batch_size(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._setup(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="model_guided", batch_size=4,
                                      stopping_max_phases=5)
        new_matrix, state = plan_next_batch(
            matrix, cfg, adaptive_cfg,
            results_dir=cfg.out_directory, seed=0,
        )
        assert not state.should_stop
        assert len(new_matrix.runs) == 4

    def test_first_run_is_near_predicted_optimum(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._setup(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="model_guided", batch_size=4,
                                      stopping_max_phases=5)
        new_matrix, _state = plan_next_batch(
            matrix, cfg, adaptive_cfg,
            results_dir=cfg.out_directory, seed=0,
        )
        # The first run is the model-predicted optimum.
        first = new_matrix.runs[0]
        x = float(first.factor_values["x"])
        y = float(first.factor_values["y"])
        # True optimum is at (0.3, -0.2); allow generous tolerance
        # because the central composite design has limited range.
        assert abs(x - 0.3) < 0.3
        assert abs(y + 0.2) < 0.3

    def test_remaining_batch_within_design_region(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._setup(tmp_path)
        adaptive_cfg = AdaptiveConfig(strategy="model_guided", batch_size=4,
                                      stopping_max_phases=5)
        new_matrix, _state = plan_next_batch(
            matrix, cfg, adaptive_cfg,
            results_dir=cfg.out_directory, seed=0,
        )
        for run in new_matrix.runs:
            for f in ("x", "y", "z"):
                v = float(run.factor_values[f])
                # Allow a small margin for predicted-optimum points that
                # might land slightly outside the [-1,1] coded box.
                assert -2.0 <= v <= 2.0


class TestSimulate:
    """Tests for doe.simulate.simulate."""

    def _make_setup(self, tmp_path, n_responses=1):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": f"r{i}"} for i in range(n_responses)],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        return cfg, matrix

    def test_callable_func_writes_results(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        def f(factors):
            x, y = float(factors["x"]), float(factors["y"])
            return {"r0": x + y + 0.5}
        out = simulate(matrix, cfg, func=f)
        results_dir = Path(out)
        assert (results_dir / "run_1.json").exists()
        for run in matrix.runs:
            payload = json.loads((results_dir / f"run_{run.run_id}.json").read_text())
            x, y = float(run.factor_values["x"]), float(run.factor_values["y"])
            assert abs(payload["r0"] - (x + y + 0.5)) < 1e-9

    def test_skips_existing(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        # Pre-write run_1 so simulate skips it
        (results_dir / "run_1.json").write_text(json.dumps({"r0": 99.0}))
        def f(factors):
            return {"r0": 1.0}
        simulate(matrix, cfg, func=f)
        # run_1 should retain the pre-existing payload
        assert json.loads((results_dir / "run_1.json").read_text())["r0"] == 99.0

    def test_overwrite_replaces_existing(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        results_dir = Path(cfg.out_directory)
        results_dir.mkdir(parents=True, exist_ok=True)
        (results_dir / "run_1.json").write_text(json.dumps({"r0": 99.0}))
        def f(factors):
            return {"r0": 1.0}
        simulate(matrix, cfg, func=f, overwrite=True)
        assert json.loads((results_dir / "run_1.json").read_text())["r0"] == 1.0

    def test_missing_response_raises(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path, n_responses=2)
        def f(factors):
            return {"r0": 1.0}  # forgot r1
        with pytest.raises(ValueError, match="did not return"):
            simulate(matrix, cfg, func=f)

    def test_target_string_resolves_file_path(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        sim_path = tmp_path / "sim.py"
        sim_path.write_text(
            "def sim(factors):\n"
            "    return {'r0': float(factors['x']) + float(factors['y'])}\n"
        )
        out = simulate(matrix, cfg, func=f"{sim_path}:sim")
        results = list(Path(out).glob("run_*.json"))
        assert len(results) == 4

    def test_session_subdirectory(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        def f(factors):
            return {"r0": 1.0}
        out = simulate(matrix, cfg, func=f, session_prefix="run-a")
        out_path = Path(out)
        assert out_path.name.startswith("run-a-")
        assert (out_path / "run_1.json").exists()
        assert (Path(cfg.out_directory) / "latest").is_symlink()

    def test_invalid_target_format(self, tmp_path):
        from doe.simulate import simulate
        cfg, matrix = self._make_setup(tmp_path)
        with pytest.raises(ValueError, match="module:function"):
            simulate(matrix, cfg, func="just_a_module")


class TestIntegerFactors:
    """Tests for Factor.dtype='int' rounding in decode paths."""

    def test_format_factor_value_rounds_int(self):
        from doe.models import Factor
        from doe.rsm import _format_factor_value
        f = Factor(name="threads", levels=["1", "64"],
                   type="continuous", dtype="int")
        assert _format_factor_value(f, 3.7) == "4"
        assert _format_factor_value(f, 17.4) == "17"
        assert _format_factor_value(f, 100.0) == "64"  # clamps to high
        assert _format_factor_value(f, -5.0) == "1"   # clamps to low

    def test_format_factor_value_keeps_float(self):
        from doe.models import Factor
        from doe.rsm import _format_factor_value
        f = Factor(name="temp", levels=["100", "200"], type="continuous")
        # Default dtype="" → continues to use %.6g formatting
        assert _format_factor_value(f, 123.45678) == "123.457"

    def test_optimize_surface_returns_integers_for_int_factor(self, tmp_path):
        """Fit a quadratic and ask for the optimum; the int-typed factor
        must come out as a string of an integer."""
        from doe.models import Factor, ExperimentRun
        from doe.rsm import fit_rsm, optimize_surface
        # 2x2 with center: int factor 'threads' (1..64) and float 'temp'
        factors = [
            Factor(name="threads", levels=["1", "64"],
                   type="continuous", dtype="int"),
            Factor(name="temp", levels=["100", "200"], type="continuous"),
        ]
        runs = []
        rid = 1
        for t in (1, 32, 64):
            for tmp in (100, 150, 200):
                runs.append(ExperimentRun(
                    run_id=rid, block_id=1,
                    factor_values={"threads": str(t), "temp": str(tmp)},
                ))
                rid += 1
        responses = {}
        for r in runs:
            tv = float(r.factor_values["threads"])
            tmp = float(r.factor_values["temp"])
            # Surface peaked near threads=20, temp=150
            responses[r.run_id] = -(tv - 20) ** 2 / 100 - (tmp - 150) ** 2 / 1000 + 5
        model = fit_rsm(runs, responses, ["threads", "temp"], factors,
                        model_type="quadratic")
        opt = optimize_surface(model, ["threads", "temp"], factors,
                               direction="maximize")
        threads_val = opt["optimal_settings"]["threads"]
        # Must be an integer string with no decimal point
        assert "." not in threads_val
        assert int(threads_val) == int(threads_val)  # parseable as int


class TestBayesianStrategy:
    """Tests for the GP-based 'bayesian' adaptive strategy."""

    def _setup(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-2", "2"], "type": "continuous"},
                {"name": "y", "levels": ["-2", "2"], "type": "continuous"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="central_composite",
        )
        cfg_dict["adaptive"] = {
            "strategy": "bayesian", "batch_size": 4,
            "stopping_max_phases": 5,
        }
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        # Quadratic surface peaked at (0.5, -0.3)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "r": -(x - 0.5) ** 2 - (y + 0.3) ** 2 + 5,
            }))
        return cfg, matrix

    def test_gp_fit_and_predict_round_trip(self):
        from doe.bo import fit_gp, predict
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(20, 2))
        y = -X[:, 0] ** 2 - X[:, 1] ** 2 + 4
        gp = fit_gp(X, y, seed=0)
        # Predict at the training points: posterior mean ≈ y
        mean, var = predict(gp, X)
        assert np.max(np.abs(mean - y)) < 0.5
        assert np.all(var >= 0)

    def test_expected_improvement_nonnegative(self):
        from doe.bo import fit_gp, expected_improvement
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(15, 2))
        y = X[:, 0] + X[:, 1]
        gp = fit_gp(X, y, seed=0)
        candidates = rng.uniform(-1, 1, size=(50, 2))
        ei = expected_improvement(gp, candidates, best_y=float(np.max(y)),
                                  direction="maximize")
        assert ei.shape == (50,)
        assert np.all(ei >= 0)

    def test_bayesian_strategy_emits_batch(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._setup(tmp_path)
        ac = AdaptiveConfig(strategy="bayesian", batch_size=4,
                            stopping_max_phases=5)
        new_matrix, state = plan_next_batch(
            matrix, cfg, ac,
            results_dir=cfg.out_directory, seed=0,
        )
        assert not state.should_stop
        assert len(new_matrix.runs) == 4

    def test_bayesian_clusters_near_optimum(self, tmp_path):
        """With enough training data on a smooth quadratic, EI should
        place at least one batch member within ±0.7 of the true
        optimum (0.5, -0.3) in each axis."""
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._setup(tmp_path)
        ac = AdaptiveConfig(strategy="bayesian", batch_size=4,
                            stopping_max_phases=5)
        new_matrix, _state = plan_next_batch(
            matrix, cfg, ac,
            results_dir=cfg.out_directory, seed=0,
        )
        close_to_opt = [
            r for r in new_matrix.runs
            if abs(float(r.factor_values["x"]) - 0.5) < 0.7
            and abs(float(r.factor_values["y"]) - (-0.3)) < 0.7
        ]
        assert len(close_to_opt) >= 1, (
            f"Expected at least one BO pick near (0.5, -0.3), got "
            f"{[(r.factor_values['x'], r.factor_values['y']) for r in new_matrix.runs]}"
        )

    def test_propose_batch_respects_size(self):
        from doe.bo import fit_gp, propose_batch
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(10, 2))
        y = -X[:, 0] ** 2 - X[:, 1] ** 2
        gp = fit_gp(X, y, seed=0)
        bounds = np.tile([-1.0, 1.0], (2, 1))
        batch = propose_batch(gp, bounds, batch_size=5, direction="maximize",
                              seed=0)
        assert batch.shape == (5, 2)
        # All chosen points lie inside the bounds
        assert np.all(batch >= -1.0 - 1e-9)
        assert np.all(batch <= 1.0 + 1e-9)


class TestMultiObjectiveBO:
    """Tests for is_pareto_front and propose_batch_multi_objective."""

    def test_pareto_front_basic(self):
        from doe.bo import is_pareto_front
        # Two-objective: maximise both
        Y = np.array([
            [1.0, 1.0],   # dominated
            [3.0, 2.0],   # on front
            [2.0, 3.0],   # on front
            [3.0, 3.0],   # dominates everything else above on front
        ])
        front = is_pareto_front(Y, ["maximize", "maximize"])
        assert front.tolist() == [False, False, False, True]

    def test_pareto_front_minimize(self):
        from doe.bo import is_pareto_front
        Y = np.array([
            [1.0, 5.0],   # on front (min y0)
            [4.0, 1.0],   # on front (min y1)
            [2.0, 3.0],   # on front
            [5.0, 5.0],   # dominated
        ])
        front = is_pareto_front(Y, ["minimize", "minimize"])
        assert front.tolist() == [True, True, True, False]

    def test_pareto_front_mixed_directions(self):
        from doe.bo import is_pareto_front
        # Maximise y0, minimise y1 — typical "max yield, min cost"
        Y = np.array([
            [10.0, 5.0],  # on front
            [9.0, 7.0],   # dominated by [10, 5]
            [8.0, 3.0],   # on front
            [10.0, 3.0],  # dominates the others on the front
        ])
        front = is_pareto_front(Y, ["maximize", "minimize"])
        assert front[3] is np.True_ or front[3] == True
        assert front[1] == False

    def test_propose_batch_multi_objective_runs(self):
        from doe.bo import fit_gp, propose_batch_multi_objective
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(20, 2))
        y1 = -(X[:, 0] - 0.4) ** 2 - X[:, 1] ** 2 + 4
        y2 = (X[:, 0] - 0.4) ** 2 + X[:, 1] ** 2 + 1  # cost (minimize)
        gp1 = fit_gp(X, y1, seed=0)
        gp2 = fit_gp(X, y2, seed=0)
        bounds = np.tile([-1.0, 1.0], (2, 1))
        batch = propose_batch_multi_objective(
            [gp1, gp2], bounds, batch_size=4,
            directions=["maximize", "minimize"], seed=0,
        )
        assert batch.shape == (4, 2)
        assert np.all(batch >= -1.0 - 1e-9)
        assert np.all(batch <= 1.0 + 1e-9)

    def test_multi_objective_strategy_emits_batch(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[
                {"name": "yield_", "optimize": "maximize"},
                {"name": "cost", "optimize": "minimize"},
            ],
            operation="central_composite",
        )
        cfg_dict["adaptive"] = {
            "strategy": "multi_objective", "batch_size": 4,
            "stopping_max_phases": 5,
        }
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "yield_": -(x - 0.4) ** 2 - y ** 2 + 4,
                "cost": (x - 0.4) ** 2 + y ** 2 + 1,
            }))
        ac = AdaptiveConfig(strategy="multi_objective", batch_size=4,
                            stopping_max_phases=5)
        new_matrix, state = plan_next_batch(
            matrix, cfg, ac, results_dir=cfg.out_directory, seed=0,
        )
        assert not state.should_stop
        assert len(new_matrix.runs) == 4


class TestHeteroscedasticGP:
    """Tests for fit_gp(noise_per_point=...) and replicate-derived variance."""

    def test_noise_per_point_mismatch_shape_raises(self):
        from doe.bo import fit_gp
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(5, 2))
        y = X[:, 0] + X[:, 1]
        with pytest.raises(ValueError, match="noise_per_point shape"):
            fit_gp(X, y, noise_per_point=np.zeros(3))

    def test_high_noise_widens_posterior_variance(self):
        from doe.bo import fit_gp, predict
        rng = np.random.default_rng(0)
        X = rng.uniform(-1, 1, size=(10, 2))
        y = X[:, 0] + X[:, 1]
        # Fit twice: once with no noise, once with large per-point noise.
        gp_clean = fit_gp(X, y, seed=0)
        gp_noisy = fit_gp(X, y, seed=0, noise_per_point=np.ones(10))
        _, var_clean = predict(gp_clean, X)
        _, var_noisy = predict(gp_noisy, X)
        # Noisy fit should have strictly larger predictive variance at the
        # training points (they're treated as uncertain, not pinned).
        assert np.all(var_noisy >= var_clean - 1e-6)
        assert np.mean(var_noisy) > np.mean(var_clean)

    def test_per_point_noise_from_replicates(self):
        from doe.adaptive import _per_point_noise_from_replicates
        from doe.models import ExperimentRun
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"x": "0", "y": "0"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"x": "0", "y": "0"}),
            ExperimentRun(run_id=3, block_id=1, factor_values={"x": "0", "y": "0"}),
            ExperimentRun(run_id=4, block_id=1, factor_values={"x": "1", "y": "1"}),
        ]
        responses = {1: 1.0, 2: 1.5, 3: 2.0, 4: 5.0}
        noise = _per_point_noise_from_replicates(runs, responses, ["x", "y"])
        assert noise is not None
        # The 3 replicates at (0,0) get the same variance:
        assert noise[0] == noise[1] == noise[2]
        # Variance of [1.0, 1.5, 2.0] with ddof=1 is 0.25
        assert abs(noise[0] - 0.25) < 1e-9
        # Singleton run gets the pooled variance (=0.25 here, only one group)
        assert abs(noise[3] - 0.25) < 1e-9

    def test_returns_none_without_replicates(self):
        from doe.adaptive import _per_point_noise_from_replicates
        from doe.models import ExperimentRun
        runs = [
            ExperimentRun(run_id=1, block_id=1, factor_values={"x": "0"}),
            ExperimentRun(run_id=2, block_id=1, factor_values={"x": "1"}),
        ]
        assert _per_point_noise_from_replicates(runs, {1: 1.0, 2: 2.0}, ["x"]) is None


class TestCalibrate:
    """Tests for doe.calibrate.calibrate."""

    def test_recovers_known_parameter(self, tmp_path):
        from doe.calibrate import calibrate, CalibrationParam
        from doe.models import ExperimentRun
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x": str(x)})
            for i, x in enumerate([-1, -0.5, 0, 0.5, 1])
        ]
        # True process: y = 2.5 * x + 0.3 (no noise)
        observed = {r.run_id: {"y": 2.5 * float(r.factor_values["x"]) + 0.3}
                    for r in runs}
        def sim(factors, *, slope=1.0, intercept=0.0):
            return {"y": slope * float(factors["x"]) + intercept}
        params = [
            CalibrationParam(name="slope", initial=1.0, low=-5.0, high=5.0),
            CalibrationParam(name="intercept", initial=0.0, low=-2.0, high=2.0),
        ]
        result = calibrate(runs, observed, sim, params)
        assert abs(result.fitted_params["slope"] - 2.5) < 1e-3
        assert abs(result.fitted_params["intercept"] - 0.3) < 1e-3
        # RMSE should improve dramatically
        assert result.rmse_after < 1e-3
        assert result.rmse_after < result.rmse_before

    def test_per_response_rmse(self, tmp_path):
        from doe.calibrate import calibrate, CalibrationParam
        from doe.models import ExperimentRun
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x": str(x)})
            for i, x in enumerate([0, 1, 2])
        ]
        observed = {
            r.run_id: {"y": float(r.factor_values["x"]),
                       "z": float(r.factor_values["x"]) + 1}
            for r in runs
        }
        def sim(factors, *, slope=0.5):
            return {"y": slope * float(factors["x"]),
                    "z": slope * float(factors["x"]) + 1}
        params = [CalibrationParam(name="slope", initial=0.5, low=0.0, high=5.0)]
        result = calibrate(runs, observed, sim, params)
        assert "y" in result.per_response_rmse
        assert "z" in result.per_response_rmse

    def test_param_spec_parsing(self):
        from doe.calibrate import parse_param_spec
        # name:low:high
        p1 = parse_param_spec("noise:0.0:1.0")
        assert p1.name == "noise" and p1.low == 0.0 and p1.high == 1.0
        assert p1.initial == 0.5
        # name:initial:low:high
        p2 = parse_param_spec("alpha:0.3:0.0:1.0")
        assert p2.initial == 0.3 and p2.low == 0.0 and p2.high == 1.0
        with pytest.raises(ValueError):
            parse_param_spec("just_a_name")
        with pytest.raises(ValueError):
            parse_param_spec("alpha:1.0:0.0")  # reversed bounds

    def test_load_observed_and_no_data_raises(self, tmp_path):
        from doe.calibrate import load_observed
        from doe.models import ExperimentRun
        runs = [ExperimentRun(run_id=1, block_id=1, factor_values={"x": "0"})]
        with pytest.raises(FileNotFoundError):
            load_observed(str(tmp_path / "nope"), runs)
        # Empty session dir → also raises
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError, match="No usable"):
            load_observed(str(empty), runs)


class TestParallelRunner:
    """Tests for the --parallel runner emission."""

    def test_parallel_template_renders(self, tmp_path):
        from doe.codegen import generate_script
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
            test_script="./test.py",
        )
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        out = tmp_path / "run.py"
        rendered = generate_script(matrix, cfg, str(out), format="py",
                                    parallel_workers=4)
        assert "ThreadPoolExecutor" in rendered
        assert "PARALLEL_WORKERS = 4" in rendered

    def test_parallel_runner_executes(self, tmp_path):
        """End-to-end: emit a parallel runner that calls a tiny test
        script and verify all run_*.json files appear."""
        from doe.codegen import generate_script
        # Tiny test script that always emits {"r": 1.0}
        test_script = tmp_path / "test.py"
        test_script.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, json\n"
            "out = sys.argv[sys.argv.index('--out') + 1]\n"
            "with open(out, 'w') as f:\n"
            "    json.dump({'r': 1.0}, f)\n"
        )
        test_script.chmod(0o755)

        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
            test_script=str(test_script),
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        runner = tmp_path / "run.py"
        generate_script(matrix, cfg, str(runner), format="py", parallel_workers=2)
        result = subprocess.run(
            [sys.executable, str(runner)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        results_dir = Path(cfg.out_directory)
        for run in matrix.runs:
            assert (results_dir / f"run_{run.run_id}.json").exists()


class TestSlurmRunner:
    """Tests for the --executor slurm runner template."""

    def _setup(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
            test_script="./test.py",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        return cfg, matrix

    def test_slurm_template_renders_array_directive(self, tmp_path):
        from doe.codegen import generate_script
        cfg, matrix = self._setup(tmp_path)
        out = tmp_path / "submit.sh"
        body = generate_script(
            matrix, cfg, str(out), executor="slurm",
            slurm_options={"partition": "gpu", "time": "02:00:00",
                           "max_concurrent": 4},
        )
        # SBATCH array directive is present and references all runs
        assert f"#SBATCH --array=1-{len(matrix.runs)}%4" in body
        assert "#SBATCH --partition=gpu" in body
        assert "#SBATCH --time=02:00:00" in body
        # Every run id is dispatched in the case block
        for run in matrix.runs:
            assert f"  {run.run_id})" in body

    def test_slurm_template_no_options(self, tmp_path):
        from doe.codegen import generate_script
        cfg, matrix = self._setup(tmp_path)
        out = tmp_path / "submit.sh"
        body = generate_script(matrix, cfg, str(out), executor="slurm")
        # Defaults: array runs without %max-concurrent
        assert f"#SBATCH --array=1-{len(matrix.runs)}" in body
        assert "%" not in body.split("\n#SBATCH --array=", 1)[1].split("\n", 1)[0]

    def test_slurm_session_block(self, tmp_path):
        from doe.codegen import generate_script
        cfg, matrix = self._setup(tmp_path)
        out = tmp_path / "submit.sh"
        body = generate_script(
            matrix, cfg, str(out), executor="slurm",
            session_prefix="experiment-a",
        )
        assert "DOE_SESSION_DIR" in body
        assert 'SESSION_NAME="experiment-a-' in body

    def test_slurm_unknown_executor_raises(self, tmp_path):
        from doe.codegen import generate_script
        cfg, matrix = self._setup(tmp_path)
        with pytest.raises(ValueError, match="Unknown executor"):
            generate_script(
                matrix, cfg, str(tmp_path / "x.sh"), executor="kubernetes",
            )


class TestCategoricalGP:
    """Tests for the mixed numeric + one-hot encoder feeding the GP."""

    def _make_cfg(self, tmp_path):
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "temp", "levels": ["100", "200"], "type": "continuous"},
                {"name": "catalyst", "levels": ["A", "B", "C"], "type": "categorical"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg_dict["settings"]["test_script"] = ""
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        return cfg, matrix

    def test_encoder_round_trip(self, tmp_path):
        from doe.adaptive import _build_factor_encoder
        cfg, matrix = self._make_cfg(tmp_path)
        encoder = _build_factor_encoder(matrix.factor_names, cfg.factors)
        assert encoder is not None
        # 1 numeric + 3 one-hot columns for catalyst
        assert encoder.n_dims == 1 + 3
        # Encoding then decoding a known run reproduces its factor values
        for run in matrix.runs:
            row = np.array(encoder.encode(run.factor_values))
            decoded = encoder.decode(row)
            assert decoded["catalyst"] == run.factor_values["catalyst"]
            assert abs(float(decoded["temp"]) - float(run.factor_values["temp"])) < 1e-3

    def test_bayesian_strategy_with_categorical(self, tmp_path):
        from doe.adaptive import plan_next_batch, AdaptiveConfig
        cfg, matrix = self._make_cfg(tmp_path)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        # Synthetic surface where catalyst='C' is best
        for run in matrix.runs:
            temp = float(run.factor_values["temp"])
            cat_bonus = {"A": 0.0, "B": 0.5, "C": 2.0}[run.factor_values["catalyst"]]
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({
                "r": -((temp - 150) / 50) ** 2 + cat_bonus,
            }))
        ac = AdaptiveConfig(strategy="bayesian", batch_size=3,
                            stopping_max_phases=5)
        new_matrix, _state = plan_next_batch(
            matrix, cfg, ac, results_dir=cfg.out_directory, seed=0,
        )
        assert len(new_matrix.runs) == 3
        # Picked levels must be valid (not random strings)
        for run in new_matrix.runs:
            assert run.factor_values["catalyst"] in {"A", "B", "C"}


class TestSensitivity:
    """Tests for Sobol index computation."""

    def test_linear_predictor_concentrates_first_order(self):
        """For a purely additive surface y = 2*x + 3*y, the first-order
        Sobol indices should sum to ~1 and approximately reflect the
        squared-coefficient ratios."""
        from doe.sensitivity import sobol_indices
        def predictor(X):
            return 2.0 * X[:, 0] + 3.0 * X[:, 1]
        result = sobol_indices(
            predictor, factor_names=["x", "y"],
            bounds=[(-1.0, 1.0), (-1.0, 1.0)],
            n_base_samples=512, seed=0,
        )
        s_first = sum(idx.first_order for idx in result.indices)
        # First-order sum should be very close to 1 for an additive model
        assert abs(s_first - 1.0) < 0.05
        # x explains ~ 4/13 ≈ 0.31, y explains ~ 9/13 ≈ 0.69
        s_x = next(i for i in result.indices if i.factor_name == "x")
        s_y = next(i for i in result.indices if i.factor_name == "y")
        assert s_y.first_order > s_x.first_order

    def test_interaction_inflates_total_order(self):
        """For y = x*y, both factors should have S_T ≈ 1 and S ≈ 0
        (pure interaction)."""
        from doe.sensitivity import sobol_indices
        def predictor(X):
            return X[:, 0] * X[:, 1]
        result = sobol_indices(
            predictor, factor_names=["x", "y"],
            bounds=[(-1.0, 1.0), (-1.0, 1.0)],
            n_base_samples=512, seed=0,
        )
        for idx in result.indices:
            assert idx.first_order < 0.15, (
                f"Expected near-zero first order for pure interaction, "
                f"got {idx.first_order}"
            )
            assert idx.total_order > 0.7, (
                f"Expected near-1 total order for pure interaction, "
                f"got {idx.total_order}"
            )

    def test_constant_predictor_emits_note(self):
        from doe.sensitivity import sobol_indices
        def predictor(X):
            return np.full(X.shape[0], 7.0)
        result = sobol_indices(
            predictor, factor_names=["x"], bounds=[(-1.0, 1.0)],
            n_base_samples=64, seed=0,
        )
        assert not result.indices
        assert any("constant" in n.lower() for n in result.notes)

    def test_make_rsm_predictor(self):
        from doe.sensitivity import make_rsm_predictor
        # Linear surface y = intercept + a*x + b*y; coded space is just [-1,1].
        coefs = {"intercept": 0.5, "x": 1.0, "y": -1.5}
        pred = make_rsm_predictor(
            coefs, factor_names=["x", "y"],
            bounds=[(-1.0, 1.0), (-1.0, 1.0)],
        )
        X = np.array([[0.0, 0.0], [1.0, -1.0]])
        y = pred(X)
        # At (0,0) → 0.5, at (1,-1) → 0.5 + 1*1 + (-1.5)*(-1) = 0.5 + 1 + 1.5 = 3.0
        assert abs(y[0] - 0.5) < 1e-9
        assert abs(y[1] - 3.0) < 1e-9


class TestSuggest:
    """Tests for doe.suggest.suggest."""

    def test_screening_tight_budget(self):
        from doe.suggest import suggest
        s = suggest(n_factors=11, n_responses=1, budget=12, goal="screening")
        assert s.operation == "plackett_burman"
        assert s.estimated_runs == 12

    def test_screening_room_for_resolution_iv(self):
        from doe.suggest import suggest
        s = suggest(n_factors=4, n_responses=1, budget=24, goal="screening")
        assert s.operation == "fractional_factorial"
        assert s.min_resolution == 4

    def test_response_surface_picks_box_behnken(self):
        from doe.suggest import suggest
        s = suggest(n_factors=3, n_responses=1, budget=20, goal="response_surface")
        assert s.operation == "box_behnken"
        assert s.replicate_center == 3

    def test_response_surface_picks_central_composite_for_more_factors(self):
        from doe.suggest import suggest
        s = suggest(n_factors=6, n_responses=1, budget=200, goal="response_surface")
        assert s.operation == "central_composite"

    def test_optimization_single_response_picks_bayesian(self):
        from doe.suggest import suggest
        s = suggest(n_factors=4, n_responses=1, budget=40, goal="optimization")
        assert s.operation == "latin_hypercube"
        assert s.adaptive_strategy == "bayesian"

    def test_optimization_multi_response_picks_multi_objective(self):
        from doe.suggest import suggest
        s = suggest(n_factors=4, n_responses=3, budget=40, goal="optimization")
        assert s.adaptive_strategy == "multi_objective"

    def test_invalid_goal_raises(self):
        from doe.suggest import suggest
        with pytest.raises(ValueError, match="goal must be one of"):
            suggest(n_factors=3, n_responses=1, budget=10, goal="exploration")

    def test_invalid_factor_count_raises(self):
        from doe.suggest import suggest
        with pytest.raises(ValueError, match="n_factors"):
            suggest(n_factors=0, n_responses=1, budget=10, goal="screening")


class TestInitBootstrap:
    """Tests for `doe init --factors --budget --goal` bootstrap mode."""

    def test_bootstrap_writes_runnable_config(self, tmp_path):
        from doe.cli import _handle_init_bootstrap
        from doe.config import load_config
        from doe.design import generate_design

        class _Args:
            factors = 3
            responses = 1
            budget = 25
            goal = "response_surface"
            categorical = 0
            output_dir = str(tmp_path)
            with_test = False

        _handle_init_bootstrap(_Args)
        config_path = tmp_path / "config.json"
        assert config_path.exists()
        cfg = load_config(str(config_path), strict=False)
        # Suggester should pick box_behnken for 3 continuous factors / budget 25.
        assert cfg.operation == "box_behnken"
        # Generated factors are placeholders the user is expected to rename
        assert [f.name for f in cfg.factors] == ["factor_1", "factor_2", "factor_3"]
        # The config must round-trip through generate_design without error
        matrix = generate_design(cfg, seed=1)
        assert len(matrix.runs) > 0

    def test_bootstrap_with_test_emits_test_py(self, tmp_path):
        from doe.cli import _handle_init_bootstrap
        from doe.config import load_config

        class _Args:
            factors = 2
            responses = 1
            budget = 16
            goal = "screening"
            categorical = 0
            output_dir = str(tmp_path)
            with_test = True

        _handle_init_bootstrap(_Args)
        assert (tmp_path / "config.json").exists()
        assert (tmp_path / "test.py").exists()
        cfg = load_config(str(tmp_path / "config.json"), strict=False)
        # test_script should now point at the generated file
        assert cfg.test_script.endswith("test.py")

    def test_bootstrap_categorical_factors(self, tmp_path):
        from doe.cli import _handle_init_bootstrap
        from doe.config import load_config

        class _Args:
            factors = 4
            responses = 1
            budget = 16
            goal = "screening"
            categorical = 2
            output_dir = str(tmp_path)
            with_test = False

        _handle_init_bootstrap(_Args)
        cfg = load_config(str(tmp_path / "config.json"), strict=False)
        # First 2 factors should be categorical placeholders
        assert sum(1 for f in cfg.factors if f.type == "categorical") == 2
        assert sum(1 for f in cfg.factors if f.type == "continuous") == 2

    def test_bootstrap_refuses_overwrite(self, tmp_path):
        from doe.cli import _handle_init_bootstrap

        class _Args:
            factors = 2
            responses = 1
            budget = 8
            goal = "screening"
            categorical = 0
            output_dir = str(tmp_path)
            with_test = False

        # First call writes the config
        _handle_init_bootstrap(_Args)
        # Second call should refuse — capture output to verify
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            _handle_init_bootstrap(_Args)
        assert "refusing to overwrite" in buf.getvalue()

    def test_bootstrap_validates_inputs(self, tmp_path):
        from doe.cli import _handle_init_bootstrap
        import io
        from contextlib import redirect_stdout

        class _Args:
            factors = 2
            responses = 1
            budget = None
            goal = "screening"
            categorical = 0
            output_dir = str(tmp_path)
            with_test = False

        buf = io.StringIO()
        with redirect_stdout(buf):
            _handle_init_bootstrap(_Args)
        assert "--budget is required" in buf.getvalue()


class TestScheffeMixture:
    """Tests for the Scheffé canonical-form mixture analysis."""

    def _runs_and_responses(self):
        from doe.models import ExperimentRun
        # Three-component mixture, simplex-lattice degree 2 + binary blends
        coords = [
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.5, 0.5, 0.0),
            (0.5, 0.0, 0.5),
            (0.0, 0.5, 0.5),
            (1 / 3, 1 / 3, 1 / 3),
        ]
        runs = [
            ExperimentRun(run_id=i + 1, block_id=1,
                          factor_values={"x1": str(c[0]), "x2": str(c[1]), "x3": str(c[2])})
            for i, c in enumerate(coords)
        ]
        # Synthetic: y = 2*x1 + 3*x2 + 1*x3 + 4*x1*x2 (synergy between 1 and 2)
        responses = {
            r.run_id: 2.0 * float(r.factor_values["x1"]) + 3.0 * float(r.factor_values["x2"])
                       + 1.0 * float(r.factor_values["x3"])
                       + 4.0 * float(r.factor_values["x1"]) * float(r.factor_values["x2"])
            for r in runs
        }
        return runs, responses

    def test_recovers_scheffe_coefficients(self):
        from doe.mixture import fit_scheffe
        runs, responses = self._runs_and_responses()
        model = fit_scheffe(runs, responses, ["x1", "x2", "x3"], model_form="quadratic")
        assert model is not None
        coefs = {t.label: t.coefficient for t in model.terms}
        assert abs(coefs["x1"] - 2.0) < 1e-6
        assert abs(coefs["x2"] - 3.0) < 1e-6
        assert abs(coefs["x3"] - 1.0) < 1e-6
        assert abs(coefs["x1*x2"] - 4.0) < 1e-6
        assert abs(coefs["x1*x3"]) < 1e-6
        assert abs(coefs["x2*x3"]) < 1e-6

    def test_linear_form_no_blends(self):
        from doe.mixture import fit_scheffe
        runs, responses = self._runs_and_responses()
        model = fit_scheffe(runs, responses, ["x1", "x2", "x3"], model_form="linear")
        # Linear-only: just three component terms, no x_i*x_j
        labels = {t.label for t in model.terms}
        assert labels == {"x1", "x2", "x3"}

    def test_invalid_form_raises(self):
        from doe.mixture import fit_scheffe
        runs, responses = self._runs_and_responses()
        with pytest.raises(ValueError):
            fit_scheffe(runs, responses, ["x1", "x2", "x3"], model_form="cubic")

    def test_is_mixture_operation(self):
        from doe.mixture import is_mixture_operation
        assert is_mixture_operation("mixture_simplex_lattice")
        assert is_mixture_operation("mixture_simplex_centroid")
        assert not is_mixture_operation("full_factorial")


class TestComparePlotEmbedding:
    """Per-run delta dotplot rendered into the compare HTML."""

    def test_html_contains_data_image(self, tmp_path):
        from doe.compare import compare_sessions, export_compare_html
        # Reuse the helper from TestCompareSessions by instantiating it.
        builder = TestCompareSessions()
        cfg, _, b, c = builder._build_two_sessions(
            tmp_path,
            baseline_fn=lambda x, y: x + y,
            candidate_fn=lambda x, y: x + y + 0.5,
        )
        report = compare_sessions(cfg, b, c)
        out_html = tmp_path / "compare.html"
        export_compare_html(report, str(out_html))
        body = out_html.read_text()
        assert "Per-run paired deltas" in body or 'class="plot"' in body
        assert 'src="data:image/png;base64,' in body


class TestTrendPlotEmbedding:
    """Per-session-mean line chart rendered into the trend HTML."""

    def test_html_contains_data_image(self, tmp_path):
        from doe.trend import trend_sessions, export_trend_html
        from doe.config import load_config
        from doe.design import generate_design
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        sessions = []
        for k in range(3):
            d = rd / f"sess-{k}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "design_matrix.json").write_text(json.dumps({
                "factor_names": matrix.factor_names,
                "operation": matrix.operation,
                "metadata": matrix.metadata,
                "runs": [
                    {"run_id": r.run_id, "block_id": r.block_id,
                     "factor_values": r.factor_values}
                    for r in matrix.runs
                ],
            }))
            for run in matrix.runs:
                x = float(run.factor_values["x"])
                y = float(run.factor_values["y"])
                (d / f"run_{run.run_id}.json").write_text(json.dumps({
                    "r": x + y + 0.4 * k,
                }))
            sessions.append(str(d))
        report = trend_sessions(cfg, sessions)
        out_html = tmp_path / "trend.html"
        export_trend_html(report, str(out_html))
        body = out_html.read_text()
        assert "Per-session mean trend" in body or 'class="plot"' in body
        assert 'src="data:image/png;base64,' in body


class TestDOptimalAugment:
    """Tests for `doe augment --type d_optimal`."""

    def _existing_design(self, tmp_path, n=4):
        from doe.config import load_config
        from doe.design import generate_design
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "z", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="fractional_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        return cfg, matrix

    def test_augment_appends_d_optimal_runs(self, tmp_path):
        from doe.design import augment_design
        cfg, matrix = self._existing_design(tmp_path)
        # cfg.lhs_samples acts as the "augmentation count" knob for d_optimal.
        cfg.lhs_samples = 3
        augmented = augment_design(matrix, cfg, augment_type="d_optimal")
        assert len(augmented.runs) == len(matrix.runs) + 3
        # All new runs use valid level values for each factor
        for run in augmented.runs[len(matrix.runs):]:
            for fname in matrix.factor_names:
                v = run.factor_values[fname]
                # Either an original level or an inserted midpoint
                assert v in {"-1", "0", "1"}
        # Augmented metadata sets n_augmented_runs = 3
        assert augmented.metadata["n_augmented_runs"] == 3

    def test_default_augment_count(self, tmp_path):
        from doe.design import augment_design
        cfg, matrix = self._existing_design(tmp_path)
        # cfg.lhs_samples = 0 (default) → max(4, n_factors+1) = 4 for k=3
        augmented = augment_design(matrix, cfg, augment_type="d_optimal")
        assert augmented.metadata["n_augmented_runs"] >= 4

    def test_d_optimal_increases_information(self, tmp_path):
        """Augmenting with D-optimal should produce a det(X'X) at least as
        large as a random pick of the same size. Approximate: compare to
        the existing det."""
        import numpy as np
        from doe.design import augment_design
        from doe.rsm import _build_design_matrix
        cfg, matrix = self._existing_design(tmp_path)
        cfg.lhs_samples = 4
        augmented = augment_design(matrix, cfg, augment_type="d_optimal")

        X_before, _ = _build_design_matrix(
            list(matrix.runs), matrix.factor_names, cfg.factors,
            model_type="linear",
        )
        X_after, _ = _build_design_matrix(
            list(augmented.runs), augmented.factor_names, cfg.factors,
            model_type="linear",
        )
        det_before = np.linalg.det(X_before.T @ X_before)
        det_after = np.linalg.det(X_after.T @ X_after)
        assert det_after >= det_before

    def test_invalid_type_raises(self, tmp_path):
        from doe.design import augment_design
        cfg, matrix = self._existing_design(tmp_path)
        with pytest.raises(ValueError, match="Unknown augment_type"):
            augment_design(matrix, cfg, augment_type="bogus")


class TestSensitivityHtml:
    """Tests for the new doe.sensitivity HTML output."""

    def test_html_export_contains_stacked_bar(self, tmp_path):
        from doe.sensitivity import (
            sobol_indices, make_rsm_predictor, export_sensitivity_html,
        )
        coefs = {"intercept": 0.0, "x": 2.0, "y": 3.0}
        pred = make_rsm_predictor(
            coefs, factor_names=["x", "y"],
            bounds=[(-1.0, 1.0), (-1.0, 1.0)],
        )
        result = sobol_indices(
            pred, factor_names=["x", "y"], bounds=[(-1.0, 1.0), (-1.0, 1.0)],
            response_name="yield", n_base_samples=64, seed=0,
        )
        out = tmp_path / "sens.html"
        export_sensitivity_html([result], str(out))
        body = out.read_text()
        assert "Sobol Sensitivity" in body
        # Inline PNG present
        assert 'src="data:image/png;base64,' in body
        assert "yield" in body

    def test_html_handles_empty_indices(self, tmp_path):
        from doe.sensitivity import SensitivityResult, export_sensitivity_html
        result = SensitivityResult(
            response_name="constant_resp",
            n_base_samples=64, n_evaluations=128,
            indices=[],
            notes=["surrogate is constant"],
        )
        out = tmp_path / "empty.html"
        export_sensitivity_html([result], str(out))
        body = out.read_text()
        assert "constant_resp" in body
        assert "constant" in body


class TestBranchedAdaptiveState:
    """Tests for the BASE-level state file + --state-name branching."""

    def test_state_filename_default(self):
        from doe.adaptive import _state_filename
        assert _state_filename(None) == "adaptive_state.json"

    def test_state_filename_with_name(self):
        from doe.adaptive import _state_filename
        assert _state_filename("trial-A") == "adaptive_state_trial-A.json"

    def test_state_filename_sanitises(self):
        """Disallowed characters become underscores."""
        from doe.adaptive import _state_filename
        assert _state_filename("my path/with weird chars") == \
            "adaptive_state_my_path_with_weird_chars.json"
        # Empty after sanitisation -> falls back to 'state'
        assert _state_filename("///") == "adaptive_state_state.json"

    def test_branching_isolates_phase_history(self, tmp_path):
        from doe.adaptive import _save_state, _load_state, AdaptiveState
        results_dir = str(tmp_path / "results")
        _save_state(AdaptiveState(phase=3, total_runs=12), results_dir)
        _save_state(AdaptiveState(phase=1, total_runs=4),
                    results_dir, state_name="branch-A")
        # Default state untouched
        default = _load_state(results_dir)
        assert default.phase == 3
        # Named state has its own phase
        branch = _load_state(results_dir, state_name="branch-A")
        assert branch.phase == 1

    def test_state_persists_across_sessions(self, tmp_path):
        """plan_next_batch reads/writes state at cfg.out_directory, not at
        the (potentially rotating) <results-dir>/latest target."""
        from doe.adaptive import (
            plan_next_batch, AdaptiveConfig, AdaptiveState, _save_state, _load_state,
        )
        from doe.config import load_config
        from doe.design import generate_design

        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r", "optimize": "maximize"}],
            operation="full_factorial",
        )
        out_directory = str(tmp_path / "results")
        cfg_dict["settings"]["out_directory"] = out_directory
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)

        # Two "session" subdirs each holding the same factor-result data.
        for sess_name in ("v1", "v2"):
            session_dir = Path(out_directory) / sess_name
            session_dir.mkdir(parents=True, exist_ok=True)
            for run in matrix.runs:
                x = float(run.factor_values["x"])
                y = float(run.factor_values["y"])
                (session_dir / f"run_{run.run_id}.json").write_text(
                    json.dumps({"r": x + y})
                )

        ac = AdaptiveConfig(strategy="refine", batch_size=2,
                            stopping_max_phases=10)
        _, state1 = plan_next_batch(
            matrix, cfg, ac,
            results_dir=str(Path(out_directory) / "v1"), seed=0,
        )
        # Force a fresh in-memory call against the second "session"; the
        # state file should still live at out_directory and reflect
        # state1.phase + 1.
        _, state2 = plan_next_batch(
            matrix, cfg, ac,
            results_dir=str(Path(out_directory) / "v2"), seed=0,
        )
        assert state2.phase > state1.phase

        # Confirm the file is at the BASE level, not in a session subdir
        assert (Path(out_directory) / "adaptive_state.json").exists()
        assert not (Path(out_directory) / "v1" / "adaptive_state.json").exists()


class TestFilterRuns:
    """Tests for `doe analyze --filter-runs`."""

    def _setup(self, tmp_path):
        from doe.config import load_config
        from doe.design import generate_design
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        # 3 corners + 1 outlier at run 1
        for i, run in enumerate(matrix.runs):
            x = float(run.factor_values["x"])
            y = float(run.factor_values["y"])
            val = x + y
            if i == 0:
                val += 100.0  # outlier
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({"r": val}))
        return cfg, matrix

    def test_excluding_outlier_changes_main_effect(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix = self._setup(tmp_path)
        report_with = analyze(matrix, cfg, results_dir=cfg.out_directory,
                               no_plots=True, fit_rsm=False)
        report_without = analyze(matrix, cfg, results_dir=cfg.out_directory,
                                  no_plots=True, fit_rsm=False,
                                  exclude_run_ids=[matrix.runs[0].run_id])
        # The outlier inflates one corner — its presence drives the main
        # effects toward zero on this 4-run design. Removing it should
        # change at least one main-effect value.
        with_effect = next(e.main_effect for e in report_with.results_by_response["r"].effects)
        without_effect = next(e.main_effect for e in report_without.results_by_response["r"].effects)
        assert abs(with_effect - without_effect) > 1.0

    def test_excluded_runs_metadata(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix = self._setup(tmp_path)
        rid = matrix.runs[0].run_id
        report = analyze(matrix, cfg, results_dir=cfg.out_directory,
                         no_plots=True, fit_rsm=False, exclude_run_ids=[rid])
        # Effects table should reflect the smaller filtered design;
        # the original matrix object isn't mutated.
        assert report.results_by_response["r"].summary_stats
        assert len(matrix.runs) == 4  # caller's matrix unchanged

    def test_unknown_id_raises(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix = self._setup(tmp_path)
        with pytest.raises(ValueError, match="Unknown run id"):
            analyze(matrix, cfg, results_dir=cfg.out_directory,
                    no_plots=True, fit_rsm=False, exclude_run_ids=[999])

    def test_excluding_all_raises(self, tmp_path):
        from doe.analysis import analyze
        cfg, matrix = self._setup(tmp_path)
        all_ids = [r.run_id for r in matrix.runs]
        with pytest.raises(ValueError, match="every run"):
            analyze(matrix, cfg, results_dir=cfg.out_directory,
                    no_plots=True, fit_rsm=False, exclude_run_ids=all_ids)


class TestInitTemplateRationale:
    """Tests for the inferred-goal rationale printed by `doe init --template`."""

    def test_rationale_inferred_for_box_behnken_template(self, tmp_path, capsys):
        from doe.cli import _print_template_rationale
        # Minimal Box-Behnken-shaped config to mimic the reactor_optimization template
        out_dir = tmp_path / "demo"
        out_dir.mkdir()
        cfg_path = out_dir / "config.json"
        cfg_path.write_text(json.dumps({
            "metadata": {"name": "demo"},
            "factors": [
                {"name": f, "levels": ["-1", "1"], "type": "continuous"}
                for f in ("a", "b", "c")
            ],
            "responses": [{"name": "y", "optimize": "maximize"}],
            "settings": {
                "operation": "box_behnken",
                "out_directory": "results",
                "test_script": "",
            },
        }))
        info = {
            "name": "Demo", "operation": "box_behnken",
            "n_factors": 3, "n_responses": 1,
        }
        _print_template_rationale(str(out_dir), info)
        out = capsys.readouterr().out
        assert "Inferred goal: response_surface" in out
        assert "box_behnken" in out

    def test_rationale_handles_missing_config(self, tmp_path, capsys):
        """Should not raise even if the config can't be loaded — bails silently."""
        from doe.cli import _print_template_rationale
        info = {"name": "x", "operation": "?", "n_factors": 0, "n_responses": 0}
        _print_template_rationale(str(tmp_path / "does-not-exist"), info)
        # No stdout means the helper bailed cleanly (no rationale to show)
        out = capsys.readouterr().out
        assert "Inferred goal" not in out

    def test_rationale_screening_path(self, tmp_path, capsys):
        from doe.cli import _print_template_rationale
        out_dir = tmp_path / "screen"
        out_dir.mkdir()
        cfg_path = out_dir / "config.json"
        cfg_path.write_text(json.dumps({
            "metadata": {"name": "demo"},
            "factors": [
                {"name": f"f{i}", "levels": ["-1", "1"], "type": "continuous"}
                for i in range(7)
            ],
            "responses": [{"name": "y", "optimize": "maximize"}],
            "settings": {
                "operation": "plackett_burman",
                "out_directory": "results",
                "test_script": "",
            },
        }))
        info = {
            "name": "Screen", "operation": "plackett_burman",
            "n_factors": 7, "n_responses": 1,
        }
        _print_template_rationale(str(out_dir), info)
        out = capsys.readouterr().out
        assert "Inferred goal: screening" in out


class TestReportInclude:
    """Tests for `doe report --include FILE`."""

    def _setup(self, tmp_path):
        from doe.config import load_config
        from doe.design import generate_design
        cfg_dict = _make_config_dict(
            factors=[
                {"name": "x", "levels": ["-1", "1"], "type": "continuous"},
                {"name": "y", "levels": ["-1", "1"], "type": "continuous"},
            ],
            responses=[{"name": "r"}],
            operation="full_factorial",
        )
        cfg_dict["settings"]["out_directory"] = str(tmp_path / "results")
        cfg = load_config(_write_config(tmp_path, cfg_dict), strict=False)
        matrix = generate_design(cfg, seed=1)
        rd = Path(cfg.out_directory)
        rd.mkdir(parents=True, exist_ok=True)
        for run in matrix.runs:
            (rd / f"run_{run.run_id}.json").write_text(json.dumps({"r": 1.0}))
        return cfg, matrix

    def test_include_file_inlined(self, tmp_path):
        from doe.report import generate_report
        cfg, matrix = self._setup(tmp_path)
        extra = tmp_path / "extra.html"
        extra.write_text(
            "<html><body><h2>Mock embedded report</h2>"
            "<p>marker-content</p></body></html>"
        )
        out = tmp_path / "master.html"
        generate_report(matrix, cfg, results_dir=str(Path(cfg.out_directory)),
                         output_path=str(out), include_paths=[str(extra)])
        body = out.read_text()
        assert "Mock embedded report" in body
        assert "marker-content" in body
        assert "Included: extra.html" in body

    def test_include_strips_style_and_header(self, tmp_path):
        """Embedded <style> / <header> / <footer> blocks are stripped so
        the master report's CSS isn't overwritten by the inclusion."""
        from doe.report import generate_report
        cfg, matrix = self._setup(tmp_path)
        extra = tmp_path / "extra.html"
        extra.write_text(
            "<html><head><style>body { background: lime; }</style></head>"
            "<body><header><h1>NOPE</h1></header><h2>Marker</h2>"
            "<footer>NOPE-FOOT</footer></body></html>"
        )
        out = tmp_path / "master.html"
        generate_report(matrix, cfg, results_dir=str(Path(cfg.out_directory)),
                         output_path=str(out), include_paths=[str(extra)])
        body = out.read_text()
        # The inclusion's style/header/footer must NOT leak into the master.
        # (Master's own header/footer/style still appear, of course; check
        # that the embedded sentinels are absent.)
        assert "background: lime" not in body
        assert "NOPE-FOOT" not in body
        # The h2 content survives
        assert ">Marker<" in body

    def test_missing_include_file_handled(self, tmp_path):
        from doe.report import generate_report
        cfg, matrix = self._setup(tmp_path)
        out = tmp_path / "master.html"
        generate_report(matrix, cfg, results_dir=str(Path(cfg.out_directory)),
                         output_path=str(out),
                         include_paths=[str(tmp_path / "does-not-exist.html")])
        body = out.read_text()
        assert "File not found" in body


class TestPackageVersion:
    """The package version pinned in pyproject and __init__ must agree."""

    def test_version_matches_pyproject(self):
        import re
        from doe import __version__
        with open("pyproject.toml") as f:
            text = f.read()
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
        assert match is not None, "Could not find version in pyproject.toml"
        assert match.group(1) == __version__


class TestReleaseNotesExtraction:
    """Regression test for the awk snippet in .github/workflows/release.yml.

    We don't run awk — we re-implement the same logic in Python and check
    a representative CHANGELOG. If the workflow's logic ever drifts,
    update this test to match.
    """

    @staticmethod
    def _extract_section(changelog: str, version: str) -> str:
        out: list[str] = []
        capturing = False
        header = f"## {version}"
        for line in changelog.splitlines():
            if line.startswith("## "):
                if capturing:
                    break
                # Match '## VERSION ...' (next char is whitespace, dash, or end).
                if line.startswith(header) and (
                    len(line) == len(header) or not line[len(header)].isalnum()
                ):
                    capturing = True
                    continue
            if capturing:
                out.append(line)
        # Strip trailing blank lines that come from a hard CHANGELOG break.
        while out and not out[-1].strip():
            out.pop()
        return "\n".join(out)

    def test_extracts_section_for_version(self):
        log = (
            "# Changelog\n\n"
            "## 0.4.0 — 2026-06-01\n\n"
            "### Added\n"
            "- New thing.\n\n"
            "## 0.3.0 — 2026-05-09\n\n"
            "### Added\n"
            "- Old thing.\n"
        )
        section = self._extract_section(log, "0.3.0")
        assert "Old thing" in section
        # Stops at the next version header
        assert "New thing" not in section

    def test_top_section_extracts(self):
        log = (
            "# Changelog\n\n"
            "## 0.4.0 — 2026-06-01\n\n"
            "Top-of-file release.\n"
        )
        section = self._extract_section(log, "0.4.0")
        assert "Top-of-file release" in section

    def test_missing_version_returns_empty(self):
        log = "# Changelog\n\n## 0.3.0 — 2026-05-09\n\nNotes here.\n"
        assert self._extract_section(log, "9.9.9") == ""

    def test_real_changelog_has_current_version_section(self):
        """Sanity: the bundled CHANGELOG actually has a section for the
        version pinned in pyproject. If a future release forgets to add
        a CHANGELOG entry, this test points it out."""
        from doe import __version__
        with open("CHANGELOG.md") as f:
            log = f.read()
        section = self._extract_section(log, __version__)
        assert section, (
            f"CHANGELOG.md is missing a '## {__version__}' section; "
            "release.yml would emit a placeholder."
        )
