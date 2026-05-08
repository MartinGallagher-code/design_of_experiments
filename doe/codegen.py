# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
import stat
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, PackageLoader

from .models import DesignMatrix, DOEConfig


def generate_script(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    output_path: str,
    format: str = "sh",
) -> str:
    template_map = {"sh": "runner_sh.j2", "py": "runner_py.j2"}
    if format not in template_map:
        raise ValueError(f"Unknown format '{format}'. Choose 'sh' or 'py'.")

    env = _jinja_env()
    template = env.get_template(template_map[format])
    context = _build_template_context(matrix, cfg)
    rendered = template.render(**context)

    _write_executable(output_path, rendered)
    return rendered


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
    rendered = template.render(**context)

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


def _build_template_context(matrix: DesignMatrix, cfg: DOEConfig) -> dict:
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
    out_directory = str(Path(cfg.out_directory or "results").resolve())
    return {
        "runs": runs_data,
        "test_script": test_script,
        "fixed_factors": cfg.fixed_factors,
        "arg_style": cfg.runner.arg_style,
        "out_directory": out_directory,
        "operation": matrix.operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(matrix.runs),
        "plan_name": cfg.metadata.get("name", ""),
    }


def _tojson(value) -> str:
    import json
    return json.dumps(value)
