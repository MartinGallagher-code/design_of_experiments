# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Drive the design from a Python function instead of an external script.

Bypasses the generated bash/python runner: imports the user-supplied
function, calls it once per design run with that run's factor values,
and writes the returned response dict to ``run_<id>.json`` — same on-disk
shape ``analyze`` already consumes.

Use cases:
* unit-testing the analysis pipeline against a known synthetic surface
* running pure-Python simulations where shelling out to a runner is
  unnecessary overhead
* iterating on the test_script logic interactively (the user can keep
  the function in their REPL and call ``simulate`` repeatedly)
"""

import datetime
import importlib
import importlib.util
import json
import os
import shutil
import sys
from typing import Any, Callable

from .models import DesignMatrix, DOEConfig, ExperimentRun


def simulate(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    func: Callable[[dict[str, str]], dict[str, float]] | str,
    output_dir: str | None = None,
    session_prefix: str | None = None,
    overwrite: bool = False,
) -> str:
    """Evaluate ``func`` once per run and persist the JSON result files.

    Parameters
    ----------
    matrix
        The design matrix.
    cfg
        The loaded config; used for ``out_directory`` and ``responses``.
    func
        Either an importable target like ``"my_module:simulate"`` /
        ``"path/to/file.py:simulate"`` or a callable directly. The target
        receives a ``dict[str, str]`` of factor values and must return a
        ``dict[str, float]`` keyed by response name.
    output_dir
        Override the destination directory. Defaults to
        ``cfg.out_directory``.
    session_prefix
        If provided, behaves like ``--session`` on ``doe generate``: a
        ``<base>/<PREFIX>-<TIMESTAMP>/`` directory is created (or
        ``<base>/<TIMESTAMP>/`` when *session_prefix* is the empty
        string) and ``<base>/latest`` is repointed.
    overwrite
        Re-evaluate runs whose result file already exists.
    """
    if isinstance(func, str):
        func_callable = _resolve_target(func)
    else:
        func_callable = func

    base_out = output_dir or cfg.out_directory or "results"
    os.makedirs(base_out, exist_ok=True)
    session_dir = base_out
    if session_prefix is not None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        session_name = (
            f"{session_prefix}-{timestamp}" if session_prefix else timestamp
        )
        session_dir = os.path.join(base_out, session_name)
        os.makedirs(session_dir, exist_ok=True)
        _update_latest_symlink(base_out, session_name)
        # Copy the design matrix into the session dir so doe analyze finds it.
        matrix_src = os.path.join(base_out, "design_matrix.json")
        if os.path.isfile(matrix_src):
            shutil.copy2(matrix_src, os.path.join(session_dir, "design_matrix.json"))

    response_names = {r.name for r in cfg.responses}
    n_done = 0
    n_skipped = 0
    n_failed: list[int] = []

    for run in matrix.runs:
        out_path = os.path.join(session_dir, f"run_{run.run_id}.json")
        if os.path.exists(out_path) and not overwrite:
            n_skipped += 1
            continue
        try:
            result = func_callable(dict(run.factor_values))
        except Exception as e:
            print(f"  Run {run.run_id} raised: {e}", file=sys.stderr)
            n_failed.append(run.run_id)
            continue
        if not isinstance(result, dict):
            raise ValueError(
                f"Simulator returned {type(result).__name__} for run "
                f"{run.run_id}; expected dict[str, float] of responses."
            )
        # Coerce to floats; surface a helpful error with the offending key.
        coerced: dict[str, float] = {}
        for key, value in result.items():
            try:
                coerced[key] = float(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Run {run.run_id}: response '{key}'={value!r} is not numeric."
                ) from None
        if response_names:
            missing = response_names - set(coerced)
            if missing:
                raise ValueError(
                    f"Run {run.run_id}: simulator did not return: {sorted(missing)}"
                )
        with open(out_path, "w") as f:
            json.dump(coerced, f, indent=2)
        n_done += 1

    print(f"Simulated {n_done} run(s); skipped {n_skipped} already-complete; "
          f"failed {len(n_failed)}{f' ({n_failed})' if n_failed else ''}.")
    print(f"Results in: {session_dir}")
    return session_dir


def _resolve_target(target: str) -> Callable[..., Any]:
    """Resolve ``module:function`` or ``path/to/file.py:function``.

    Module form is loaded via ``importlib.import_module`` (so the user's
    PYTHONPATH controls discovery); file-path form via spec-from-file so
    ad-hoc scripts work without sys.path tweaking.
    """
    if ":" not in target:
        raise ValueError(
            f"Simulator target must be 'module:function' or 'path.py:function', "
            f"got {target!r}."
        )
    module_part, _, func_name = target.rpartition(":")
    if module_part.endswith(".py") or "/" in module_part or os.sep in module_part:
        if not os.path.isfile(module_part):
            raise FileNotFoundError(
                f"Simulator file not found: '{module_part}'"
            )
        spec = importlib.util.spec_from_file_location("__doe_simulator__", module_part)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load simulator from '{module_part}'")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(module_part)

    if not hasattr(module, func_name):
        raise AttributeError(
            f"Simulator module has no '{func_name}' attribute."
        )
    func = getattr(module, func_name)
    if not callable(func):
        raise TypeError(f"Simulator target '{target}' is not callable.")
    return func


def _update_latest_symlink(base_out: str, session_name: str) -> None:
    latest = os.path.join(base_out, "latest")
    try:
        if os.path.islink(latest):
            os.unlink(latest)
        elif os.path.lexists(latest):
            print(
                f"Warning: {latest} exists and is not a symlink; not updating.",
                file=sys.stderr,
            )
            return
        os.symlink(session_name, latest)
    except OSError as e:
        print(f"Warning: could not update {latest}: {e}", file=sys.stderr)
