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
    dtype: str = ""             # "" (auto) | "int" | "float"


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
    sweep_points: int = 0                    # 0 = auto: use lhs_samples or default 8
    min_resolution: int = 0                  # 0 = auto (max within smallest run budget); 3/4/5+ = pin
    metadata: dict = field(default_factory=dict)
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    adaptive: object = None                  # AdaptiveConfig | None


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
class OrdinalTrendResult:
    factor_name: str
    response_name: str
    linear_coefficient: float
    linear_ss: float
    linear_f_value: float | None = None
    linear_p_value: float | None = None
    quadratic_coefficient: float = 0.0
    quadratic_ss: float = 0.0
    quadratic_f_value: float | None = None
    quadratic_p_value: float | None = None
    r_squared_linear: float = 0.0
    r_squared_quadratic: float = 0.0


@dataclass
class KneePointResult:
    factor_name: str
    response_name: str
    knee_value: float
    knee_response: float
    ci_low: float
    ci_high: float
    r_squared: float
    segment1_slope: float
    segment2_slope: float
    method: str = "piecewise_linear"


@dataclass
class ModelAdequacy:
    """Post-fit diagnostics for the response surface model fitted in analyze."""
    model_type: str                  # "linear" | "quadratic"
    n_observations: int
    n_parameters: int
    r_squared: float
    adj_r_squared: float
    predicted_r_squared: float       # 1 - PRESS/SS_total
    press: float
    shapiro_w: float | None = None
    shapiro_p: float | None = None
    durbin_watson: float | None = None
    runorder_drift_slope: float | None = None
    runorder_drift_p: float | None = None
    max_leverage: float = 0.0
    leverage_threshold: float = 0.0  # 2 * p / n
    high_leverage_run_ids: list[int] = field(default_factory=list)
    max_cooks_distance: float = 0.0
    cooks_threshold: float = 0.0     # 4 / n
    high_influence_run_ids: list[int] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class StationaryPoint:
    """Characterization of the stationary point of a quadratic RSM."""
    nature: str                                    # "maximum" | "minimum" | "saddle" | "ridge" | "rising_ridge" | "flat"
    coded_location: dict[str, float]               # in [-1, 1] coded space
    natural_location: dict[str, str]               # decoded into factor units
    predicted_value: float
    eigenvalues: list[float]
    eigenvectors: list[list[float]]                # rows align with eigenvalues; cols align with factor_names order
    factor_order: list[str]                        # order of factors in eigenvectors
    inside_design_region: bool                     # True iff |x*| <= 1 in every coded coord
    ridge_direction: dict[str, float] | None = None  # unit vector along the indeterminate axis when nature involves a ridge


@dataclass
class AchievedPowerEntry:
    factor_name: str
    n_levels: int
    power_at_delta: float       # power at the chosen delta
    mde_at_target: float        # minimum detectable effect at target_power


@dataclass
class AchievedPower:
    """Post-hoc statistical power, computed from the actual residual MS."""
    n_runs: int
    df_error: int
    residual_ms: float
    sigma: float                # sqrt(residual_ms)
    alpha: float
    delta: float                # the effect size used to report power_at_delta
    target_power: float         # the power level used to back out MDE
    per_factor: list[AchievedPowerEntry] = field(default_factory=list)


@dataclass
class ResponseAnalysis:
    response_name: str
    effects: list[EffectResult]
    summary_stats: dict
    interactions: list[InteractionEffect] = field(default_factory=list)
    anova_table: AnovaTable | None = None
    ordinal_trends: list[OrdinalTrendResult] = field(default_factory=list)
    model_adequacy: ModelAdequacy | None = None
    stationary_point: StationaryPoint | None = None
    achieved_power: AchievedPower | None = None


@dataclass
class AnalysisReport:
    results_by_response: dict[str, ResponseAnalysis]
    pareto_chart_paths: dict[str, str] = field(default_factory=dict)
    effects_plot_paths: dict[str, str] = field(default_factory=dict)
    normal_plot_paths: dict[str, str] = field(default_factory=dict)
    half_normal_plot_paths: dict[str, str] = field(default_factory=dict)
    diagnostics_plot_paths: dict[str, str] = field(default_factory=dict)
    knee_point_results: dict[str, list[KneePointResult]] = field(default_factory=dict)
    knee_point_plot_paths: dict[str, str] = field(default_factory=dict)
    ordinal_trend_plot_paths: dict[str, str] = field(default_factory=dict)
    alias_structure: "AliasStructure | None" = None


@dataclass
class AliasEntry:
    """One row of the alias / confounding report.

    `effect` is a single main effect or two-factor interaction. `aliased_with`
    lists every other effect this one is correlated with above the reporting
    threshold, paired with the absolute correlation magnitude in coded space
    (1.0 means perfect aliasing; values in (0, 1) are partial aliasing as
    seen in Plackett-Burman designs).
    """
    effect: str
    aliased_with: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class AliasStructure:
    design_type: str                    # "fractional_factorial" | "plackett_burman"
    resolution: int | None = None       # III, IV, V, ... (None for PB or when undetermined)
    notes: list[str] = field(default_factory=list)
    main_effects: list[AliasEntry] = field(default_factory=list)
    two_factor_interactions: list[AliasEntry] = field(default_factory=list)


@dataclass
class PerRunDelta:
    """One matched-run row in a session comparison."""
    run_key: str                          # canonical "factor=value, factor=value" key
    baseline_run_id: int
    candidate_run_id: int
    baseline_value: float
    candidate_value: float
    delta: float                          # candidate - baseline


@dataclass
class EffectDelta:
    """Change in a main effect between baseline and candidate sessions."""
    factor_name: str
    baseline_effect: float
    candidate_effect: float
    delta: float                          # candidate - baseline
    flipped_sign: bool                    # True iff sign changed and both magnitudes are non-trivial


@dataclass
class DeltaDecomposition:
    """Results of regressing y ~ session + Σ x_i + Σ session*x_i.

    Splits the candidate-vs-baseline delta into a uniform intercept shift
    and per-factor slope (effect-size) changes, with p-values from the
    pooled regression. Approximates the existing mean_delta and per-factor
    EffectDelta numbers, but with proper standard errors.
    """
    n_observations: int
    df_error: int
    intercept_shift: float
    intercept_shift_p: float | None
    slope_shifts: list[tuple[str, float, float | None]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ResponseComparison:
    response_name: str
    n_baseline: int
    n_candidate: int
    n_matched: int
    baseline_mean: float
    candidate_mean: float
    mean_delta: float
    paired_t_stat: float | None = None
    paired_p_value: float | None = None
    cohens_d: float | None = None
    per_run: list[PerRunDelta] = field(default_factory=list)
    effect_deltas: list[EffectDelta] = field(default_factory=list)
    decomposition: DeltaDecomposition | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class ComparisonReport:
    baseline_dir: str
    candidate_dir: str
    factor_names: list[str]
    n_baseline_runs: int
    n_candidate_runs: int
    n_matched_runs: int
    responses: list[ResponseComparison] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
