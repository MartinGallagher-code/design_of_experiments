from dataclasses import dataclass, field


@dataclass
class Factor:
    name: str
    levels: list[str]


@dataclass
class DOEConfig:
    factors: list[Factor]
    static_settings: list[str]
    block_count: int
    test_script: str
    operation: str
    processed_directory: str
    out_directory: str


@dataclass
class ExperimentRun:
    run_id: int
    block_id: int
    factor_values: dict[str, str]
    static_settings: list[str]


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


@dataclass
class AnalysisReport:
    effects: list[EffectResult]
    summary_stats: dict
    pareto_chart_path: str | None = None
    effects_plot_path: str | None = None
