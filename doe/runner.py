# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Helpers for user-authored Python test scripts.

A test script invoked by the generated runner receives factor values
(via CLI args or environment variables, depending on ``runner.arg_style``)
and must write a JSON file at the ``--out`` path containing one numeric
value per response.

This module hides the wiring:

    from doe.runner import parse_factors, emit

    factors, out = parse_factors(["threads", "batch_size"])
    throughput = run_my_test(int(factors["threads"]), int(factors["batch_size"]))
    emit(out, throughput=throughput)
"""

import argparse
import json
import os
import sys
from collections.abc import Iterable


_VALID_STYLES = ("double-dash", "env", "positional")


def parse_factors(
    factor_names: Iterable[str],
    fixed_factor_names: Iterable[str] = (),
    arg_style: str = "double-dash",
    argv: list[str] | None = None,
) -> tuple[dict[str, str], str]:
    """Parse the runner's invocation and return ``(factor_values, out_path)``.

    Values are returned as strings — cast them yourself (``int(...)``,
    ``float(...)``) so the conversion is visible in the test script.

    Parameters
    ----------
    factor_names
        Names of the experiment factors, in the order they were declared
        in the config.
    fixed_factor_names
        Names of fixed factors (passed to the script but typically constant).
    arg_style
        ``"double-dash"`` (``--name value``), ``"env"`` (uppercase env vars),
        or ``"positional"``.
    argv
        Override ``sys.argv[1:]`` (useful for tests).
    """
    if arg_style not in _VALID_STYLES:
        raise ValueError(
            f"arg_style must be one of {_VALID_STYLES}, got {arg_style!r}"
        )

    factor_names = list(factor_names)
    fixed_factor_names = list(fixed_factor_names)
    argv = sys.argv[1:] if argv is None else list(argv)

    if arg_style == "double-dash":
        parser = argparse.ArgumentParser()
        parser.add_argument("--out", required=True)
        for name in factor_names + fixed_factor_names:
            parser.add_argument(f"--{name}", required=True, dest=name)
        ns = parser.parse_args(argv)
        values = {name: getattr(ns, name) for name in factor_names}
        return values, ns.out

    if arg_style == "env":
        parser = argparse.ArgumentParser()
        parser.add_argument("--out", required=True)
        ns, _ = parser.parse_known_args(argv)
        missing = [n for n in factor_names if n.upper() not in os.environ]
        if missing:
            raise SystemExit(
                f"Missing environment variables for factors: "
                f"{', '.join(n.upper() for n in missing)}"
            )
        values = {name: os.environ[name.upper()] for name in factor_names}
        return values, ns.out

    # positional
    if "--out" not in argv:
        raise SystemExit("missing --out PATH at end of argv")
    cut = argv.index("--out")
    positional = argv[:cut]
    if len(argv) < cut + 2:
        raise SystemExit("missing PATH after --out")
    out_path = argv[cut + 1]
    expected = len(factor_names) + len(fixed_factor_names)
    if len(positional) != expected:
        raise SystemExit(
            f"expected {expected} positional argument(s) "
            f"({', '.join(factor_names + fixed_factor_names)}), "
            f"got {len(positional)}"
        )
    values = {name: positional[i] for i, name in enumerate(factor_names)}
    return values, out_path


def emit(
    out_path: str,
    responses: dict[str, float] | None = None,
    *,
    _expected: Iterable[str] | None = None,
    **kwargs: float,
) -> None:
    """Write the response values as JSON to *out_path*.

    Either pass a dict (useful when response names aren't valid Python
    identifiers) or keyword arguments::

        emit(out_path, throughput=42.0, latency=1.2)
        emit(out_path, {"cpu-util": 0.83, "p99-latency": 12.5})

    If *_expected* is provided, missing or extra response keys raise
    ``ValueError`` so typos are caught before downstream analysis.
    """
    if responses is None:
        responses = kwargs
    elif kwargs:
        raise TypeError("emit(): pass either a responses dict or keyword args, not both")

    if _expected is not None:
        expected = set(_expected)
        got = set(responses)
        missing = expected - got
        extra = got - expected
        if missing or extra:
            parts = []
            if missing:
                parts.append(f"missing: {sorted(missing)}")
            if extra:
                parts.append(f"unexpected: {sorted(extra)}")
            raise ValueError(f"emit() response mismatch ({'; '.join(parts)})")

    coerced: dict[str, float] = {}
    for name, value in responses.items():
        try:
            coerced[name] = float(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"emit(): response '{name}'={value!r} is not numeric ({e})"
            ) from None

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(coerced, f, indent=2)
