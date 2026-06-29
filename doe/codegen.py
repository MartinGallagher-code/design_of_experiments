# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

from .models import DesignMatrix, DOEConfig


def generate_script(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    output_path: str,
    format: str = "sh",
    session_prefix: str | None = None,
    parallel_workers: int = 1,
    executor: str = "local",
    slurm_options: dict[str, Any] | None = None,
) -> str:
    """Render a runner script that drives the user's test_script.

    When *session_prefix* is not None, the runner creates a fresh
    timestamped subdirectory under the configured ``out_directory`` for
    each invocation and updates a ``latest`` symlink to point at it.
    A *session_prefix* of "" produces a bare-timestamp subdirectory
    (no prefix); pass a string to label the session.

    When *parallel_workers* > 1 (with the default ``local`` executor) the
    format is forced to a Python ``concurrent.futures.ThreadPoolExecutor``-
    based runner which submits runs in parallel.

    When *executor* is ``"slurm"`` the output is an ``sbatch`` array
    submission script. ``slurm_options`` may include keys
    ``partition``, ``time``, ``cpus_per_task``, ``mem``,
    ``max_concurrent``, ``job_name``, ``log_dir``, and
    ``extra_directives`` (a list of raw ``#SBATCH`` arguments).
    """
    if executor not in ("local", "slurm"):
        raise ValueError(
            f"Unknown executor '{executor}'. Choose 'local' or 'slurm'."
        )

    if executor == "slurm":
        template_name = "runner_slurm.j2"
    elif parallel_workers > 1:
        template_name = "runner_parallel_py.j2"
    else:
        template_map = {"sh": "runner_sh.j2", "py": "runner_py.j2"}
        if format not in template_map:
            raise ValueError(f"Unknown format '{format}'. Choose 'sh' or 'py'.")
        template_name = template_map[format]

    env = _jinja_env()
    template = env.get_template(template_name)
    context = _build_template_context(matrix, cfg, session_prefix=session_prefix)
    context["parallel_workers"] = parallel_workers
    if executor == "slurm":
        opts = slurm_options or {}
        plan_name = str(cfg.metadata.get("name") or "doe")
        log_dir = opts.get("log_dir") or os.path.join(
            os.path.dirname(output_path) or ".", "slurm-logs",
        )
        context.update({
            "slurm_script_basename": os.path.basename(output_path),
            "slurm_job_name": opts.get("job_name", _slurm_safe_job_name(plan_name)),
            "slurm_partition": opts.get("partition", ""),
            "slurm_time": opts.get("time", ""),
            "slurm_cpus_per_task": opts.get("cpus_per_task", 0) or 0,
            "slurm_mem": opts.get("mem", ""),
            "slurm_max_concurrent": opts.get("max_concurrent", 0) or 0,
            "slurm_log_dir": log_dir,
            "slurm_extra_directives": list(opts.get("extra_directives", []) or []),
        })

    rendered: str = template.render(**context)

    _write_executable(output_path, rendered)
    return rendered


def _slurm_safe_job_name(name: str) -> str:
    """Sanitise a string into a Slurm-friendly job name (alphanumeric + dash)."""
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-"
                      for ch in name).strip("-")
    return cleaned[:32] or "doe"


def generate_test_scaffold(cfg: DOEConfig, output_path: str, language: str = "py") -> str:
    """Generate a starter test_script for the user, prefilled from the config.

    The user only has to edit the TODO block to plug in their real test.
    """
    template_map = {"py": "scaffold_py.j2", "sh": "scaffold_sh.j2"}
    if language not in template_map:
        raise ValueError(f"Unknown language '{language}'. Choose 'py' or 'sh'.")

    env = _jinja_env()
    template = env.get_template(template_map[language])
    context = {
        "factor_names": [f.name for f in cfg.factors],
        "fixed_factor_names": list(cfg.fixed_factors.keys()),
        "response_names": [r.name for r in cfg.responses],
        "arg_style": cfg.runner.arg_style,
        "plan_name": cfg.metadata.get("name", ""),
    }
    rendered: str = template.render(**context)

    _write_executable(output_path, rendered)
    return rendered


def _jinja_env() -> Environment:
    env = Environment(
        loader=PackageLoader("doe", "templates"),
        keep_trailing_newline=True,
    )
    env.filters["tojson"] = _tojson
    env.filters["py_ident"] = _py_ident
    env.filters["sh_var"] = _sh_var
    return env


def _write_executable(output_path: str, contents: str) -> None:
    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(contents)
    path = Path(output_path)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def generate_config_template(output_path: str) -> dict[str, Any]:
    """Write an annotated starter config.json the user can edit.

    The template is a runnable config (sensible defaults) that also documents
    its decision points: every option-style field has a sibling ``_<key>_options``
    listing alternatives separated by ``|``.  ``fixed_factors`` mirrors the
    factor names with their first level so the user can move entries between
    ``factors`` and ``fixed_factors`` by deleting/restoring lines.
    """
    template = _blank_config_template()

    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        import json
        json.dump(template, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return template


def _blank_config_template() -> dict[str, Any]:
    """Return the in-memory template dict.  Public for testing."""
    factors = [
        {
            "name": "temperature",
            "type": "numeric",
            "unit": "C",
            "levels": ["100", "200"],
            "description": "Continuous numeric factor — list [low, high]",
            "_type_options": "numeric | categorical",
        },
        {
            "name": "pressure",
            "type": "numeric",
            "unit": "atm",
            "levels": ["1", "5"],
            "description": "Continuous numeric factor — list [low, high]",
        },
        {
            "name": "catalyst",
            "type": "categorical",
            "unit": "",
            "levels": ["A", "B", "C"],
            "description": "Categorical factor — list each discrete choice",
        },
    ]

    fixed_factors = {name: levels[0] for name, levels in
                     ((f["name"], f["levels"]) for f in factors)}

    return {
        "_help": (
            "Starter config generated by 'doe scaffold-config'. "
            "Replace sample names/values, then run 'doe info --config config.json' "
            "to verify. Fields beginning with '_' are documentation and are "
            "ignored by the loader. Values containing ' | ' list alternatives — "
            "pick one. The fixed_factors block mirrors the factor names so you "
            "can move an entry between 'factors' (varied) and 'fixed_factors' "
            "(held constant) by deleting/restoring the corresponding line."
        ),
        "metadata": {
            "name": "My Experiment",
            "description": "Short description of what you're testing",
        },
        "factors": factors,
        "fixed_factors": fixed_factors,
        "responses": [
            {
                "name": "yield",
                "unit": "%",
                "optimize": "maximize",
                "weight": 1.0,
                "description": "Higher is better",
                "_optimize_options": "maximize | minimize",
            },
            {
                "name": "cost",
                "unit": "$",
                "optimize": "minimize",
                "weight": 1.0,
                "description": "Lower is better",
            },
        ],
        "settings": {
            "operation": "full_factorial",
            "_operation_options": (
                "full_factorial | plackett_burman | latin_hypercube | "
                "central_composite | fractional_factorial | box_behnken | "
                "definitive_screening | taguchi | d_optimal | "
                "mixture_simplex_lattice | mixture_simplex_centroid | "
                "linear_sweep | log_sweep"
            ),
            "block_count": 1,
            "test_script": "./test.py",
            "out_directory": "results",
            "processed_directory": "results",
            "lhs_samples": 0,
            "sweep_points": 0,
            "_help": (
                "block_count: split the runs into N randomised blocks (1 = no blocking). "
                "test_script: path to the script the runner calls (see 'doe scaffold-test'). "
                "lhs_samples: only used by latin_hypercube (0 = auto). "
                "sweep_points: only used by linear_sweep / log_sweep (0 = auto)."
            ),
        },
        "runner": {
            "arg_style": "double-dash",
            "_arg_style_options": "double-dash | env | positional",
            "result_file": "json",
            "_help": (
                "arg_style controls how the runner passes factor values to "
                "test_script. double-dash: --name value. env: NAME=value. "
                "positional: value1 value2 ... --out PATH."
            ),
        },
        "_adaptive_help": (
            "Optional: uncomment the 'adaptive' block below for sequential "
            "experimentation (run a small batch, analyse, plan the next batch). "
            "Remove the leading underscore from '_adaptive' to enable."
        ),
        "_adaptive": {
            "strategy": "refine",
            "_strategy_options": "refine | explore | balanced",
            "batch_size": 4,
            "stopping_effect_threshold": 0.0,
            "stopping_power_threshold": 0.0,
            "stopping_max_phases": 10,
            "response_name": None,
        },
    }


def _py_ident(name: str) -> str:
    """Sanitize a name into a valid Python identifier."""
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    if not out or out[0].isdigit():
        out = "_" + out
    return out


def _sh_var(name: str) -> str:
    """Sanitize a name into an uppercase shell variable name."""
    out = "".join(c if c.isalnum() or c == "_" else "_" for c in name).upper()
    if not out or out[0].isdigit():
        out = "_" + out
    return out


def _build_template_context(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    session_prefix: str | None = None,
) -> dict[str, Any]:
    runs_data = [
        {
            "run_id": run.run_id,
            "block_id": run.block_id,
            "factor_values": run.factor_values,
        }
        for run in matrix.runs
    ]
    # Resolve to absolute paths so the generated script works from any directory
    test_script = str(Path(cfg.test_script).resolve()) if cfg.test_script else ""
    base_out_directory = str(Path(cfg.out_directory or "results").resolve())
    return {
        "runs": runs_data,
        "test_script": test_script,
        "fixed_factors": cfg.fixed_factors,
        "arg_style": cfg.runner.arg_style,
        "base_out_directory": base_out_directory,
        # Kept for backwards compatibility with any external templates.
        "out_directory": base_out_directory,
        "session_prefix": session_prefix,
        "operation": matrix.operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(matrix.runs),
        "plan_name": cfg.metadata.get("name", ""),
    }


def _tojson(value: Any) -> str:
    import json
    return json.dumps(value)
