# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass, field


@dataclass
class Factor:
    name: str
    levels: list[str]
    type: str = "categorical"   # categorical | continuous | ordinal
    description: str = ""
    unit: str = ""


@dataclass
class ResponseVar:
    name: str
    optimize: str = "maximize"  # maximize | minimize
    unit: str = ""
    description: str = ""
    weight: float = 1.0
    bounds: list[float] | None = None  # [low, high] for desirability


@dataclass
class RunnerConfig:
    arg_style: str = "double-dash"  # double-dash | env | positional
    result_file: str = "json"


@dataclass
class DOEConfig:
    factors: list[Factor]
    fixed_factors: dict[str, str]
    responses: list[ResponseVar]
    block_count: int
    test_script: str
    operation: str
    processed_directory: str
    out_directory: str
    lhs_samples: int = 0                    # 0 = auto: max(10, 2 * n_factors)
    metadata: dict = field(default_factory=dict)
    runner: RunnerConfig = field(default_factory=RunnerConfig)


@dataclass
class ExperimentRun:
    run_id: int
    block_id: int
    factor_values: dict[str, str]


@dataclass
class DesignMatrix:
    runs: list[ExperimentRun]
    factor_names: list[str]
    operation: str
    metadata: dict = field(default_factory=dict)


@dataclass
class EffectResult:
    factor_name: str
    main_effect: float
    std_error: float
    pct_contribution: float
    ci_low: float = 0.0
    ci_high: float = 0.0


@dataclass
class InteractionEffect:
    factor_a: str
    factor_b: str
    interaction_effect: float
    pct_contribution: float


@dataclass
class AnovaRow:
    source: str
    df: int
    ss: float
    ms: float
    f_value: float | None = None
    p_value: float | None = None


@dataclass
class AnovaTable:
    rows: list[AnovaRow]
    error_row: AnovaRow | None = None
    total_row: AnovaRow | None = None
    lack_of_fit_row: AnovaRow | None = None
    pure_error_row: AnovaRow | None = None
    error_method: str = "pooled"  # "pooled", "lenth", "replicates"


@dataclass
class ResponseAnalysis:
    response_name: str
    effects: list[EffectResult]
    summary_stats: dict
    interactions: list[InteractionEffect] = field(default_factory=list)
    anova_table: AnovaTable | None = None


@dataclass
class AnalysisReport:
    results_by_response: dict[str, ResponseAnalysis]
    pareto_chart_paths: dict[str, str] = field(default_factory=dict)
    effects_plot_paths: dict[str, str] = field(default_factory=dict)
    normal_plot_paths: dict[str, str] = field(default_factory=dict)
    half_normal_plot_paths: dict[str, str] = field(default_factory=dict)
    diagnostics_plot_paths: dict[str, str] = field(default_factory=dict)
