#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run multi-objective optimization for all use cases and update HTML pages."""

import subprocess
import os
import re
import glob
import json
import html as html_module


def find_html_file(uc_dir_name, html_dir="website/use-cases"):
    """Find the HTML file for a use case, trying numbered and unnumbered names."""
    # Try numbered: 01_reactor_optimization -> 01-reactor-optimization.html
    html_name = uc_dir_name.replace("_", "-")
    path = os.path.join(html_dir, f"{html_name}.html")
    if os.path.exists(path):
        return path

    # Try unnumbered: 01_reactor_optimization -> reactor-optimization.html
    parts = uc_dir_name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        unnumbered = parts[1].replace("_", "-")
        path = os.path.join(html_dir, f"{unnumbered}.html")
        if os.path.exists(path):
            return path

    return None


def run_multi_opt(config_path):
    """Run doe.py optimize --multi and return stdout."""
    result = subprocess.run(
        ["python", "doe.py", "optimize", "--config", config_path, "--multi"],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout
    if "MULTI-OBJECTIVE" in output:
        return output
    return None


def insert_multi_opt_into_html(html_path, multi_opt_text):
    """Insert multi-objective results into the HTML page."""
    with open(html_path, "r") as f:
        content = f.read()

    # Skip if already has multi-objective section
    if "Multi-Objective Optimization" in content:
        return False

    escaped = html_module.escape(multi_opt_text)

    multi_section = (
        '\n    <h3>Multi-Objective Optimization</h3>\n'
        '    <div class="code-block"><div class="code-header">'
        '<span>doe optimize --multi</span></div>'
        '<div class="code-body" style="font-size:.72rem;line-height:1.5;">'
        f'{escaped}</div></div>\n'
    )

    # Find the last </section> before chapter-nav and insert before it
    # Pattern: </section> ... <div class="chapter-nav">
    # There may be <!-- Nav --> comment, blank lines, etc. between them
    m = re.search(
        r'(  </section>\s*(?:<!-- Nav -->\s*)?  <div class="chapter-nav">)',
        content
    )
    if m:
        original = m.group(1)
        replacement = multi_section + original
        content = content.replace(original, replacement, 1)
        with open(html_path, "w") as f:
            f.write(content)
        return True

    return False


def main():
    configs = sorted(glob.glob("doe/use_cases/*/config.json"))
    html_dir = "website/use-cases"

    success = 0
    skipped = 0
    failed = 0
    no_html = 0
    fail_list = []

    for cfg_path in configs:
        uc_dir = os.path.basename(os.path.dirname(cfg_path))

        # Check if it has 2+ responses
        with open(cfg_path) as f:
            cfg = json.load(f)
        if len(cfg.get("responses", [])) < 2:
            skipped += 1
            continue

        # Find matching HTML file
        html_path = find_html_file(uc_dir, html_dir)
        if not html_path:
            no_html += 1
            fail_list.append(f"  NO HTML: {uc_dir}")
            continue

        # Run multi-objective optimization
        try:
            multi_output = run_multi_opt(cfg_path)
        except Exception as e:
            failed += 1
            fail_list.append(f"  ERROR {uc_dir}: {e}")
            continue

        if not multi_output:
            failed += 1
            fail_list.append(f"  NO OUTPUT: {uc_dir}")
            continue

        # Insert into HTML
        if insert_multi_opt_into_html(html_path, multi_output):
            success += 1
        else:
            failed += 1
            fail_list.append(f"  INSERT FAIL: {uc_dir} -> {html_path}")

    print(f"Success: {success}, Skipped (single response): {skipped}, "
          f"Failed: {failed}, No HTML: {no_html}")
    if fail_list:
        print("\nFailures:")
        for line in fail_list:
            print(line)


if __name__ == "__main__":
    main()
