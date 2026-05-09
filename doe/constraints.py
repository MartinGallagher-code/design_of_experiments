# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Constraint expressions for filtering generated experimental runs.

Each constraint is a Python expression string that references factor
names and evaluates to a boolean. Numeric factor values are bound as
floats; string-only values stay as ``str``. The expression is parsed
with :mod:`ast` and walked with an explicit allow-list of node types
so users cannot smuggle in attribute access, function calls, or
imports — only arithmetic, comparisons, boolean logic, and ``in``
membership tests.

Example expressions::

    "x + y <= 1"                       # mixture-style sum cap
    "catalyst != 'A' or temperature <= 150"  # conditional cap
    "x * y >= 0"                       # quadrant restriction
"""

import ast
from typing import Any

from .models import ExperimentRun


_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Compare,
    ast.And, ast.Or, ast.Not,
    ast.USub, ast.UAdd,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
    ast.Constant, ast.Name, ast.Load,
    ast.Tuple, ast.List, ast.Set,
)


class ConstraintError(ValueError):
    """Raised when a constraint expression is malformed or uses unsafe syntax."""


def parse_constraint(expression: str) -> ast.Expression:
    """Parse and validate a constraint expression. Returns the AST."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ConstraintError(
            f"Invalid constraint syntax: {expression!r} ({e.msg})"
        ) from None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise ConstraintError(
                f"Constraint {expression!r} uses disallowed syntax: "
                f"{type(node).__name__}. Only arithmetic, comparisons, "
                "and boolean logic referencing factor names are allowed."
            )
    return tree


def evaluate_constraint(
    tree: ast.Expression,
    factor_values: dict[str, str],
    expression: str = "",
) -> bool:
    """Evaluate a parsed constraint against a single run's factor values.

    Numeric-looking values are converted to ``float`` so expressions like
    ``x + y <= 1`` work even when factor values are stored as strings.
    """
    namespace: dict[str, Any] = {}
    for name, value in factor_values.items():
        try:
            namespace[name] = float(value)
        except (TypeError, ValueError):
            namespace[name] = value
    try:
        # Compile the validated AST — eval'd against an empty builtins dict
        # so attribute access / imports cannot run even if a future code
        # path bypasses the AST walk.
        code = compile(tree, "<constraint>", "eval")
        result = eval(code, {"__builtins__": {}}, namespace)
    except NameError as e:
        raise ConstraintError(
            f"Constraint {expression!r} references unknown factor: {e}"
        ) from None
    except Exception as e:
        raise ConstraintError(
            f"Constraint {expression!r} failed to evaluate: {e}"
        ) from None
    return bool(result)


def filter_runs(
    runs: list[ExperimentRun],
    constraints: list[str],
) -> tuple[list[ExperimentRun], list[ExperimentRun]]:
    """Split ``runs`` into ``(kept, dropped)`` according to the constraint set.

    A run is kept only if every constraint evaluates to True for its
    factor values.
    """
    if not constraints:
        return list(runs), []
    parsed = [(expr, parse_constraint(expr)) for expr in constraints]
    kept: list[ExperimentRun] = []
    dropped: list[ExperimentRun] = []
    for run in runs:
        ok = True
        for expr, tree in parsed:
            if not evaluate_constraint(tree, run.factor_values, expr):
                ok = False
                break
        (kept if ok else dropped).append(run)
    return kept, dropped
