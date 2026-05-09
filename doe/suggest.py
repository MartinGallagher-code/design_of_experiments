# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recommend a DOE design given factor count, run budget, and goal.

Encodes the standard "which design should I use?" decision tree from
Box, Hunter & Hunter into a small heuristic so users don't need to
memorise the trade-offs:

  * **Screening** (lots of factors, very small budget): Plackett-Burman
    when factors are 2-level and the budget is tight; fractional
    factorial when the budget allows a clean Resolution-IV design.
  * **Response surface** (continuous factors, modest budget, want a
    quadratic surface): Box-Behnken if k=3..5 and a 2-level corner
    isn't desired; central composite when corners + axials are
    affordable.
  * **Optimisation** (open-ended search): suggest an adaptive
    fractional-factorial seed plus the bayesian / multi_objective
    strategy depending on how many responses the user has.

Returns a ``Suggestion`` object listing the operation, run count, any
recommended block / replicate counts, and short rationale text. The CLI
formats it as advice; the user still has to write the config.
"""

from dataclasses import dataclass, field


GOALS = ("screening", "response_surface", "optimization")


@dataclass
class Suggestion:
    operation: str
    estimated_runs: int
    rationale: list[str] = field(default_factory=list)
    block_count: int = 1
    replicate_center: int = 0
    min_resolution: int = 0
    adaptive_strategy: str | None = None
    notes: list[str] = field(default_factory=list)


def suggest(
    n_factors: int,
    n_responses: int,
    budget: int,
    goal: str = "screening",
    factor_kinds: list[str] | None = None,
) -> Suggestion:
    """Pick a DOE design based on the user's situation.

    Parameters
    ----------
    n_factors
        Total factor count.
    n_responses
        Response count (>1 nudges towards multi_objective for optim goals).
    budget
        Maximum number of runs the user can afford.
    goal
        ``"screening"`` (which factors matter?), ``"response_surface"``
        (fit a quadratic and find an optimum within bounds), or
        ``"optimization"`` (open-ended sequential search).
    factor_kinds
        Optional list of ``"continuous"`` / ``"categorical"`` (one per
        factor). Defaults to all-continuous.
    """
    if n_factors < 1:
        raise ValueError("n_factors must be >= 1")
    if budget < 1:
        raise ValueError("budget must be >= 1")
    if goal not in GOALS:
        raise ValueError(
            f"goal must be one of {GOALS}, got {goal!r}"
        )
    factor_kinds = factor_kinds or ["continuous"] * n_factors

    n_continuous = sum(1 for k in factor_kinds if k == "continuous")
    n_categorical = sum(1 for k in factor_kinds if k != "continuous")

    if goal == "screening":
        return _suggest_screening(n_factors, budget, n_continuous, n_categorical)
    if goal == "response_surface":
        return _suggest_response_surface(
            n_factors, budget, n_continuous, n_categorical,
        )
    return _suggest_optimization(
        n_factors, n_responses, budget, n_continuous, n_categorical,
    )


def _suggest_screening(n_factors, budget, n_cont, n_cat):
    """Lots of factors, small budget — pick a 2-level screening design."""
    rationale: list[str] = [
        f"Goal: screening — identify which of {n_factors} factor(s) matter.",
    ]
    # Plackett-Burman runs come in multiples of 4 and need at most n_factors+3 columns.
    pb_runs = ((n_factors + 4) // 4) * 4
    pb_runs = max(pb_runs, 8)

    # 2^(k-p) fractional factorial: smallest power of 2 >= n_factors + 1.
    ff_runs = 1
    while ff_runs < max(n_factors + 1, 8):
        ff_runs *= 2

    # Recommend PB when budget can afford it but not the smallest FF —
    # PB squeezes more main effects into fewer runs than FF can.
    if pb_runs <= budget < ff_runs:
        return Suggestion(
            operation="plackett_burman",
            estimated_runs=pb_runs,
            rationale=rationale + [
                f"Budget ({budget}) fits a Plackett-Burman ({pb_runs} runs) "
                f"but not the smallest fractional factorial ({ff_runs} runs). "
                "PB is a saturated 2-level design estimating main effects only.",
            ],
            notes=[
                "PB confounds main effects with two-factor interactions. "
                "Run 'doe analyze' afterwards and check the alias structure.",
            ],
        )

    runs = ff_runs
    if budget >= 2 * runs:
        return Suggestion(
            operation="fractional_factorial",
            estimated_runs=2 * runs,
            min_resolution=4,
            rationale=rationale + [
                f"Budget ({budget}) allows {2 * runs} runs — request "
                "Resolution IV so main effects are clean of two-factor "
                "interactions (settings.min_resolution=4).",
            ],
        )
    return Suggestion(
        operation="fractional_factorial",
        estimated_runs=runs,
        min_resolution=3,
        rationale=rationale + [
            f"Budget ({budget}) supports {runs} runs — Resolution III "
            "will mix main effects with 2FIs; consider a follow-up "
            "fold-over if any effect looks active.",
        ],
        notes=[
            "Run 'doe analyze' and inspect the alias structure section "
            "before acting on a 'significant main effect'.",
        ],
    )


def _suggest_response_surface(n_factors, budget, n_cont, n_cat):
    rationale: list[str] = [
        f"Goal: response surface — fit a quadratic over {n_factors} factor(s).",
    ]
    if n_cat > 0:
        rationale.append(
            f"{n_cat} categorical factor(s) detected; consider treating "
            "them as fixed_factors and running a numeric-only RSM."
        )
    if n_cont == 0:
        return Suggestion(
            operation="full_factorial",
            estimated_runs=2 ** n_factors,
            rationale=rationale + [
                "All factors are categorical — RSM doesn't apply; fall "
                "back to a full factorial."
            ],
        )

    # Box-Behnken: rotatable, three-level, runs = 2 k (k-1) + n_centre for k>=3.
    if 3 <= n_cont <= 5:
        bb_runs = {3: 13, 4: 25, 5: 41}[n_cont]
        if budget >= bb_runs:
            return Suggestion(
                operation="box_behnken",
                estimated_runs=bb_runs,
                replicate_center=3,
                rationale=rationale + [
                    f"Box-Behnken on {n_cont} continuous factors uses "
                    f"{bb_runs} runs (incl. 3 centre points) — rotatable "
                    "and avoids the cube corners.",
                ],
            )

    # Central composite: corners + axials + centre.
    cc_runs = 2 ** n_cont + 2 * n_cont + 5
    if budget >= cc_runs:
        return Suggestion(
            operation="central_composite",
            estimated_runs=cc_runs,
            replicate_center=5,
            rationale=rationale + [
                f"Central composite on {n_cont} continuous factors uses "
                f"~{cc_runs} runs (corners + axials + 5 centre).",
            ],
        )

    # Definitive screening — efficient 3-level surrogate when the budget
    # is small and we still want to detect curvature.
    if n_cont >= 3:
        ds_runs = 2 * n_cont + 1
        return Suggestion(
            operation="definitive_screening",
            estimated_runs=ds_runs,
            rationale=rationale + [
                f"Budget ({budget}) is too small for a Box-Behnken/CCD; "
                f"definitive screening fits {ds_runs} runs and still "
                "detects main effects + curvature.",
            ],
        )

    return Suggestion(
        operation="full_factorial",
        estimated_runs=3 ** n_cont,
        replicate_center=0,
        rationale=rationale + [
            f"Few factors — a 3-level full factorial on {n_cont} factors "
            f"uses {3 ** n_cont} runs and supports a quadratic.",
        ],
    )


def _suggest_optimization(n_factors, n_responses, budget, n_cont, n_cat):
    rationale: list[str] = [
        f"Goal: optimisation — sequential search over {n_factors} factor(s).",
    ]

    seed_runs = max(2 * n_factors + 1, 8)
    if seed_runs >= budget:
        return Suggestion(
            operation="latin_hypercube",
            estimated_runs=min(seed_runs, budget),
            rationale=rationale + [
                f"Budget too small for an iterative loop ({budget} runs). "
                "A space-filling Latin hypercube uses every run on a one-shot "
                "exploration of the factor space.",
            ],
        )

    # Reasonable mix: 1/3 of the budget on the seed, 2/3 on adaptive batches.
    seed = max(seed_runs, budget // 3)
    seed = min(seed, max(2 ** n_factors, seed_runs))
    strategy = "multi_objective" if n_responses > 1 else "bayesian"
    return Suggestion(
        operation="latin_hypercube",
        estimated_runs=seed,
        adaptive_strategy=strategy,
        rationale=rationale + [
            f"Seed with a Latin hypercube ({seed} runs), then iterate "
            f"with the '{strategy}' adaptive strategy. Each follow-up "
            f"batch uses Expected Improvement on a GP surrogate fit to "
            f"the runs you've already done — typical batch size 4–8.",
        ],
        notes=[
            "Add an 'adaptive' block to your config to enable iterative "
            "batching. After running the seed, call 'doe next-batch'.",
        ],
    )
