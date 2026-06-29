# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Alias / confounding structure for two-level screening designs.

For a two-level design (every factor at -1/+1), each main effect column and
every two-factor interaction column is computed in coded space, then the
absolute Pearson correlation between every pair is examined. A correlation
of 1.0 is full aliasing; 0 is orthogonality; values in between mark partial
aliasing (typical in Plackett-Burman designs).

The same routine handles both fractional factorial (full aliases) and
Plackett-Burman (partial aliases) designs.
"""

from itertools import combinations

import numpy as np

from .models import AliasEntry, AliasStructure, DesignMatrix


def compute_alias_structure(
    matrix: DesignMatrix,
    factor_names: list[str] | None = None,
    threshold: float = 0.05,
    full_alias_tol: float = 1e-6,
) -> AliasStructure | None:
    """Compute the alias structure of a two-level design.

    Parameters
    ----------
    matrix
        The design matrix.
    factor_names
        Optional override for the factor names. Defaults to ``matrix.factor_names``.
    threshold
        Absolute correlation magnitude below which an alias is suppressed.
        0.05 keeps the report compact while still surfacing meaningful
        partial aliases.
    full_alias_tol
        Absolute correlation distance from 1.0 within which two columns are
        treated as fully aliased (i.e., perfectly confounded).

    Returns ``None`` if the design isn't a two-level screening design or has
    fewer than two factors (so there are no two-factor interactions).
    """
    if matrix.operation not in ("fractional_factorial", "plackett_burman"):
        return None
    names = list(factor_names or matrix.factor_names)
    n_factors = len(names)
    if n_factors < 2 or not matrix.runs:
        return None

    # Build the coded ±1 design matrix from the runs. We require a two-level
    # design; if any factor doesn't have exactly two distinct levels, bail.
    levels_per_factor: list[list[str]] = []
    for f in names:
        vals: list[str] = []
        seen: set[str] = set()
        for run in matrix.runs:
            v = run.factor_values.get(f)
            if v is not None and v not in seen:
                seen.add(v)
                vals.append(v)
        if len(vals) != 2:
            return None
        levels_per_factor.append(sorted(vals))  # deterministic low/high

    n_runs = len(matrix.runs)
    Z = np.zeros((n_runs, n_factors))
    for i, run in enumerate(matrix.runs):
        for j, f in enumerate(names):
            v = run.factor_values[f]
            low, _high = levels_per_factor[j]
            Z[i, j] = -1.0 if v == low else 1.0

    # Build column labels and values: main effects + 2-factor interactions
    me_labels = list(names)
    twofi_pairs: list[tuple[int, int]] = list(combinations(range(n_factors), 2))
    twofi_labels = [f"{names[a]}*{names[b]}" for a, b in twofi_pairs]

    me_cols = Z
    twofi_cols = np.column_stack([Z[:, a] * Z[:, b] for a, b in twofi_pairs])
    cols = np.column_stack([me_cols, twofi_cols])
    labels = me_labels + twofi_labels

    # Pearson-like correlation in coded space. Each column has zero mean and
    # unit norm sqrt(n) when the design is balanced; computing dot/||a||/||b||
    # generalises to PB centre points / unbalanced cases too.
    norms = np.linalg.norm(cols, axis=0)
    safe = norms > 0
    if not np.all(safe):
        # A column with zero variance can't participate in correlation
        # computation. Drop it and remember why.
        keep = np.where(safe)[0]
        cols = cols[:, keep]
        labels = [labels[i] for i in keep]
        norms = norms[keep]
    R = (cols.T @ cols) / np.outer(norms, norms)
    np.fill_diagonal(R, 0.0)
    R_abs = np.abs(R)

    # Pull out alias entries. We iterate main effects first, then two-factor
    # interactions, listing only effects with absolute correlation above the
    # reporting threshold.
    n_me = len(me_labels)

    def _entries(start: int, end: int) -> list[AliasEntry]:
        out: list[AliasEntry] = []
        for i in range(start, end):
            partners: list[tuple[str, float]] = []
            for j in range(len(labels)):
                if i == j:
                    continue
                r = float(R_abs[i, j])
                if r >= threshold:
                    partners.append((labels[j], r))
            partners.sort(key=lambda t: -t[1])
            out.append(AliasEntry(effect=labels[i], aliased_with=partners))
        return out

    main_entries = _entries(0, n_me)
    twofi_entries = _entries(n_me, len(labels))

    # Determine resolution for FF: based on highest-order word that's fully
    # aliased with the intercept (constant column). pyDOE3 already encodes
    # this in the design construction, so a quick stand-in: use the lowest
    # order alias seen.
    resolution: int | None = None
    notes: list[str] = []
    if matrix.operation == "fractional_factorial":
        full_aliases_me_to_2fi = any(
            (1.0 - r) < full_alias_tol
            for entry in main_entries
            for partner, r in entry.aliased_with
            if "*" in partner
        )
        full_aliases_among_2fi = any(
            (1.0 - r) < full_alias_tol
            for entry in twofi_entries
            for partner, r in entry.aliased_with
            if "*" in partner
        )
        if full_aliases_me_to_2fi:
            resolution = 3
            notes.append(
                "Resolution III: main effects are aliased with two-factor "
                "interactions. A significant 'main effect' could be the "
                "interaction in disguise."
            )
        elif full_aliases_among_2fi:
            resolution = 4
            notes.append(
                "Resolution IV: main effects are clean of two-factor "
                "interactions, but 2FIs are aliased in pairs."
            )
        else:
            resolution = 5
            notes.append(
                "Resolution V or higher: main effects and 2FIs are all "
                "estimable independently."
            )
    else:
        notes.append(
            "Plackett-Burman: main effects are orthogonal to each other but "
            "partially correlated with two-factor interactions. Treat large "
            "main effects with caution unless you can confirm with a "
            "follow-up resolution-V design."
        )

    return AliasStructure(
        design_type=matrix.operation,
        resolution=resolution,
        notes=notes,
        main_effects=main_entries,
        two_factor_interactions=twofi_entries,
    )
