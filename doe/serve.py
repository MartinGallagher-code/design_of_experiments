# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tiny stdlib HTTP server for browsing DOE result sessions.

``doe serve --root results/`` starts a localhost server that lists every
session subdirectory in *root* and links to any rendered HTML reports
(``report.html``, ``compare.html``, ``trend.html``) plus a directory
index for raw ``run_*.json`` files.

Stays on stdlib (``http.server``) so there's no new dependency. Bind
defaults to ``127.0.0.1`` so the server isn't exposed externally; the
user can opt into ``--host 0.0.0.0`` if they really want it visible.
"""

from __future__ import annotations

import html
import http.server
import os
import io
import socketserver
from functools import partial


def serve(root: str, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Block serving the contents of *root*. Press Ctrl-C to stop."""
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Root directory not found: '{root}'")
    abs_root = os.path.abspath(root)

    handler_factory = partial(_DoeHandler, directory=abs_root)
    with socketserver.TCPServer((host, port), handler_factory) as httpd:
        print(f"Serving {abs_root} at http://{host}:{port}/  (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


class _DoeHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with a custom index for the root path."""

    def list_directory(self, path: str | os.PathLike[str]) -> io.BytesIO | None:
        # Only customise the *root* directory listing; subfolders fall
        # through to the default handler so the user can still browse
        # individual run_*.json files.
        try:
            same = os.path.samefile(path, self.directory)
        except (OSError, ValueError):
            same = False
        if not same:
            return super().list_directory(path)

        try:
            entries = sorted(os.listdir(path))
        except OSError:
            self.send_error(404, "Could not list directory")
            return None

        sessions: list[tuple[str, str | None]] = []  # (name, report_path)
        for name in entries:
            full = os.path.join(path, name)
            if not os.path.isdir(full):
                continue
            report = None
            for candidate in ("report.html", "compare.html", "trend.html"):
                if os.path.isfile(os.path.join(full, candidate)):
                    report = candidate
                    break
            sessions.append((name, report))

        body = _render_index(sessions)
        encoded = body.encode("utf-8", errors="replace")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return io.BytesIO(encoded)


def _render_index(sessions: list[tuple[str, str | None]]) -> str:
    rows = ""
    for name, report in sessions:
        link_name = html.escape(name)
        if report:
            row = (
                f'<tr><td><a href="{link_name}/{html.escape(report)}">{link_name}</a></td>'
                f'<td><a href="{link_name}/">browse files</a></td>'
                f'<td class="muted">{html.escape(report)}</td></tr>'
            )
        else:
            row = (
                f'<tr><td>{link_name}</td>'
                f'<td><a href="{link_name}/">browse files</a></td>'
                f'<td class="muted">no report</td></tr>'
            )
        rows += row + "\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DOE Sessions</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; padding: 24px 40px; color: #2c3e50; }}
    h1 {{ color: steelblue; }}
    table {{ border-collapse: collapse; min-width: 500px; }}
    th, td {{ border-bottom: 1px solid #dce1e8; padding: 8px 12px; text-align: left; }}
    th {{ background: #f4f7fa; }}
    a {{ color: steelblue; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .muted {{ color: #888; font-size: 0.92em; }}
    .empty {{ color: #888; padding: 16px; }}
  </style>
</head>
<body>
  <h1>DOE Sessions</h1>
  {('<table><thead><tr><th>Session</th><th>Files</th><th>Report</th></tr></thead><tbody>'
    + rows + '</tbody></table>') if sessions
    else '<p class="empty">No session subdirectories found in this folder.</p>'}
</body>
</html>
"""
