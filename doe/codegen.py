import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .models import DesignMatrix, DOEConfig

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_script(
    matrix: DesignMatrix,
    cfg: DOEConfig,
    output_path: str,
    format: str = "sh",
) -> str:
    template_map = {"sh": "runner_sh.j2", "py": "runner_py.j2"}
    if format not in template_map:
        raise ValueError(f"Unknown format '{format}'. Choose 'sh' or 'py'.")

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    env.filters["tojson"] = _tojson

    template = env.get_template(template_map[format])
    context = _build_template_context(matrix, cfg)
    rendered = template.render(**context)

    with open(output_path, "w") as f:
        f.write(rendered)

    path = Path(output_path)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return rendered


def _build_template_context(matrix: DesignMatrix, cfg: DOEConfig) -> dict:
    runs_data = [
        {
            "run_id": run.run_id,
            "block_id": run.block_id,
            "factor_values": run.factor_values,
        }
        for run in matrix.runs
    ]
    return {
        "runs": runs_data,
        "test_script": cfg.test_script,
        "fixed_factors": cfg.fixed_factors,
        "arg_style": cfg.runner.arg_style,
        "out_directory": cfg.out_directory or "results",
        "operation": matrix.operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(matrix.runs),
        "plan_name": cfg.metadata.get("name", ""),
    }


def _tojson(value) -> str:
    import json
    return json.dumps(value)
