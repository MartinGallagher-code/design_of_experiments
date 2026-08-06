# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration tests for end-to-end DOE workflows."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from doe.analysis import analyze
from doe.config import load_config
from doe.design import generate_design
from doe.models import DOEConfig, Factor, ResponseVar
from doe.rsm import fit_rsm, optimize_surface
from doe.report import generate_report


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_config():
    """Create a simple 3-factor, 2-response config for testing."""
    return DOEConfig(
        factors=[
            Factor(name="temp", levels=["100", "200"]),
            Factor(name="pressure", levels=["1", "2"]),
            Factor(name="catalyst", levels=["A", "B"]),
        ],
        fixed_factors={},
        responses=[
            ResponseVar(name="yield", optimize="maximize"),
            ResponseVar(name="cost", optimize="minimize"),
        ],
        block_count=1,
        test_script="test.sh",
        operation="full_factorial",
        processed_directory="",
        out_directory="results",
    )


@pytest.fixture
def simple_latin_config():
    """Create a Latin hypercube config with continuous factors."""
    return DOEConfig(
        factors=[
            Factor(name="x1", levels=["0", "10"], type="continuous"),
            Factor(name="x2", levels=["0", "10"], type="continuous"),
        ],
        fixed_factors={},
        responses=[
            ResponseVar(name="y", optimize="maximize"),
        ],
        block_count=1,
        test_script="test.sh",
        operation="latin_hypercube",
        processed_directory="",
        out_directory="results",
        lhs_samples=10,
    )


def create_mock_results(matrix, temp_dir, response_name="yield"):
    """Create mock result JSON files for a design matrix."""
    results_dir = temp_dir / "results"
    results_dir.mkdir(exist_ok=True)

    for i, run in enumerate(matrix.runs):
        result = {response_name: float(80 + i)}
        result_file = results_dir / f"run_{run.run_id}.json"
        with open(result_file, "w") as f:
            json.dump(result, f)


def test_full_factorial_workflow(simple_config, temp_dir):
    """Test complete full-factorial design workflow."""
    simple_config.out_directory = str(temp_dir / "results")

    # 1. Generate design
    matrix = generate_design(simple_config, seed=42)
    assert len(matrix.runs) == 8  # 2^3 full factorial
    assert matrix.operation == "full_factorial"
    assert matrix.factor_names == ["temp", "pressure", "catalyst"]

    # 2. Create mock results
    create_mock_results(matrix, temp_dir)

    # 3. Analyze
    report = analyze(
        matrix=matrix,
        cfg=simple_config,
        results_dir=str(temp_dir / "results"),
        no_plots=True,
    )
    assert report is not None
    assert "yield" in report.results_by_response


def test_latin_hypercube_workflow(simple_latin_config, temp_dir):
    """Test Latin hypercube design workflow."""
    simple_latin_config.out_directory = str(temp_dir / "results")

    # 1. Generate design
    matrix = generate_design(simple_latin_config, seed=42)
    assert len(matrix.runs) == 10  # LHS with lhs_samples=10
    assert matrix.operation == "latin_hypercube"

    # 2. Create mock results
    create_mock_results(matrix, temp_dir)

    # 3. Analyze
    report = analyze(
        matrix=matrix,
        cfg=simple_latin_config,
        results_dir=str(temp_dir / "results"),
        no_plots=True,
    )
    assert report is not None


def test_rsm_optimization_workflow(simple_config, temp_dir):
    """Test response surface modeling and optimization."""
    simple_config.out_directory = str(temp_dir / "results")

    # 1. Generate design
    matrix = generate_design(simple_config, seed=42)

    # 2. Create results
    create_mock_results(matrix, temp_dir)

    # 3. Fit RSM
    responses = {
        i + 1: float(80 + i) for i in range(len(matrix.runs))
    }
    model = fit_rsm(
        runs=matrix.runs,
        responses=responses,
        factor_names=matrix.factor_names,
        factors=simple_config.factors,
        model_type="linear",
    )
    assert model is not None
    assert model.r_squared >= 0

    # 4. Optimize surface
    optimum = optimize_surface(
        model=model,
        factor_names=matrix.factor_names,
        factors=simple_config.factors,
        direction="maximize",
    )
    assert "optimal_settings" in optimum
    assert "predicted_value" in optimum


def test_multi_response_analysis(simple_config, temp_dir):
    """Test analysis with multiple responses."""
    simple_config.out_directory = str(temp_dir / "results")

    # 1. Generate design
    matrix = generate_design(simple_config, seed=42)

    # 2. Create results with multiple responses
    results_dir = temp_dir / "results"
    results_dir.mkdir(exist_ok=True)
    for i, run in enumerate(matrix.runs):
        result = {"yield": float(80 + i), "cost": float(100 - i)}
        result_file = results_dir / f"run_{run.run_id}.json"
        with open(result_file, "w") as f:
            json.dump(result, f)

    # 3. Analyze
    report = analyze(
        matrix=matrix,
        cfg=simple_config,
        results_dir=str(results_dir),
        no_plots=True,
    )
    assert "yield" in report.results_by_response
    assert "cost" in report.results_by_response


def test_design_metadata(simple_config):
    """Test that design metadata is properly recorded."""
    matrix = generate_design(simple_config, seed=42)

    assert matrix.metadata["n_factors"] == 3
    assert matrix.metadata["n_total_runs"] == 8
    assert matrix.metadata["seed"] == 42


def test_design_reproducibility(simple_config):
    """Test that designs with same seed are reproducible."""
    matrix1 = generate_design(simple_config, seed=42)
    matrix2 = generate_design(simple_config, seed=42)

    assert len(matrix1.runs) == len(matrix2.runs)
    assert matrix1.factor_names == matrix2.factor_names

    # Verify run order is identical
    for r1, r2 in zip(matrix1.runs, matrix2.runs):
        assert r1.factor_values == r2.factor_values


def test_html_report_generation(simple_config, temp_dir):
    """Test HTML report generation."""
    simple_config.out_directory = str(temp_dir / "results")

    # 1. Generate design and results
    matrix = generate_design(simple_config, seed=42)
    create_mock_results(matrix, temp_dir)

    # 2. Analyze
    analyze(
        matrix=matrix,
        cfg=simple_config,
        results_dir=str(temp_dir / "results"),
        no_plots=True,
    )

    # 3. Generate report
    report_path = temp_dir / "report.html"
    generate_report(
        matrix=matrix,
        cfg=simple_config,
        results_dir=str(temp_dir / "results"),
        output_path=str(report_path),
    )

    # Verify report was created
    assert report_path.exists()
    assert report_path.stat().st_size > 0

    # Verify HTML contains expected content
    with open(report_path) as f:
        content = f.read()
        assert "yield" in content or "Design Summary" in content
