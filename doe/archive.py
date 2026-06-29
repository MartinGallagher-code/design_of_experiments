# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reproducible session archives.

Bundles a session directory (``run_*.json`` + ``design_matrix.json``)
together with the config, the runner script, and any rendered HTML/CSV
report into a single tarball with a manifest summarising what's inside.
The tarball is sufficient to re-run ``doe analyze``/``doe report`` on
another machine: paste the config and the result files back in place
and re-invoke.
"""

import datetime
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path
from typing import Any



def archive_session(
    session_dir: str,
    output_path: str,
    config_path: str | None = None,
    extras: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bundle a session into a tar.gz with a manifest. Returns the manifest dict."""
    if not os.path.isdir(session_dir):
        raise FileNotFoundError(f"Session directory not found: '{session_dir}'")

    files: list[tuple[str, str]] = []  # (arcname, abspath)
    for entry in sorted(Path(session_dir).rglob("*")):
        if entry.is_file():
            arcname = "session/" + str(entry.relative_to(session_dir))
            files.append((arcname, str(entry)))

    if config_path:
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Config not found: '{config_path}'")
        files.append((f"config/{os.path.basename(config_path)}", config_path))

    for extra in extras or []:
        if not os.path.isfile(extra):
            print(f"Warning: skipping missing extra '{extra}'")
            continue
        files.append((f"extras/{os.path.basename(extra)}", extra))

    file_records = []
    for arcname, abspath in files:
        size = os.path.getsize(abspath)
        sha = _sha256_of_file(abspath)
        file_records.append({
            "arcname": arcname, "size": size, "sha256": sha,
        })

    manifest = {
        "tool": "doe",
        "format_version": 1,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_dir": os.path.abspath(session_dir),
        "config_path": os.path.abspath(config_path) if config_path else None,
        "files": file_records,
        "metadata": metadata or {},
    }

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as tar:
        for arcname, abspath in files:
            tar.add(abspath, arcname=arcname)

        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=False).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        info.mtime = int(datetime.datetime.now().timestamp())
        tar.addfile(info, io.BytesIO(manifest_bytes))

    return manifest


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
