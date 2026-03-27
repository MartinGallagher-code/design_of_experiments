#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate website HTML pages for use cases 27-86 and inject experimental matrices into all use case pages (1-86)."""
import json, os, glob, html, subprocess, re

from doe.config import load_config
from doe.design import generate_design

DESIGN_LABELS = {
    "box_behnken": "Box-Behnken Design",
    "central_composite": "Central Composite Design",
    "full_factorial": "Full Factorial Design",
    "fractional_factorial": "Fractional Factorial Design",
    "plackett_burman": "Plackett-Burman Design",
    "latin_hypercube": "Latin Hypercube Design",
    "definitive_screening": "Definitive Screening Design",
    "taguchi": "Taguchi Orthogonal Array",
    "d_optimal": "D-Optimal Design",
    "mixture_simplex_lattice": "Simplex-Lattice Mixture Design",
    "mixture_simplex_centroid": "Simplex-Centroid Mixture Design",
}

HERO_STYLES = {
    "cloud": ("linear-gradient(135deg, #dbeafe, #bfdbfe)", "rgba(29,78,216,.12)", "#1d4ed8", "&#x2601;"),
    "data": ("linear-gradient(135deg, #d1fae5, #a7f3d0)", "rgba(5,150,105,.12)", "#059669", "&#x1F4CA;"),
    "networking": ("linear-gradient(135deg, #ede9fe, #ddd6fe)", "rgba(124,58,237,.12)", "#7c3aed", "&#x1F310;"),
    "security": ("linear-gradient(135deg, #fee2e2, #fecaca)", "rgba(220,38,38,.12)", "#dc2626", "&#x1F6E1;"),
    "iot": ("linear-gradient(135deg, #cffafe, #a5f3fc)", "rgba(8,145,178,.12)", "#0891b2", "&#x1F4E1;"),
    "devops": ("linear-gradient(135deg, #fae8ff, #f0abfc)", "rgba(192,38,211,.12)", "#c026d3", "&#x2699;"),
    "food": ("linear-gradient(135deg, #fef3c7, #fde68a)", "rgba(217,119,6,.12)", "#d97706", "&#x1F373;"),
    "agriculture": ("linear-gradient(135deg, #d9f99d, #bef264)", "rgba(101,163,13,.12)", "#65a30d", "&#x1F331;"),
    "health": ("linear-gradient(135deg, #fce7f3, #fbcfe8)", "rgba(219,39,119,.12)", "#db2777", "&#x1F3CB;"),
    "automotive": ("linear-gradient(135deg, #fed7aa, #fdba74)", "rgba(234,88,12,.12)", "#ea580c", "&#x1F697;"),
    "environment": ("linear-gradient(135deg, #bbf7d0, #86efac)", "rgba(22,163,74,.12)", "#16a34a", "&#x1F30D;"),
    "home": ("linear-gradient(135deg, #e0e7ff, #c7d2fe)", "rgba(79,70,229,.12)", "#4f46e5", "&#x1F3E0;"),
    "photography": ("linear-gradient(135deg, #fef9c3, #fde047)", "rgba(202,138,4,.12)", "#ca8a04", "&#x1F4F7;"),
    "music": ("linear-gradient(135deg, #fce4ec, #f8bbd0)", "rgba(194,24,91,.12)", "#c2185b", "&#x1F3B5;"),
    "petcare": ("linear-gradient(135deg, #fff3e0, #ffe0b2)", "rgba(230,81,0,.12)", "#e65100", "&#x1F43E;"),
    "textiles": ("linear-gradient(135deg, #f3e5f5, #e1bee7)", "rgba(142,36,170,.12)", "#8e24aa", "&#x1F9F5;"),
    "chemistry": ("linear-gradient(135deg, #e8f5e9, #c8e6c9)", "rgba(46,125,50,.12)", "#2e7d32", "&#x1F9EA;"),
    "woodworking": ("linear-gradient(135deg, #fef3c7, #fde68a)", "rgba(180,83,9,.12)", "#b45309", "&#x1FA93;"),
    "sports": ("linear-gradient(135deg, #dbeafe, #93c5fd)", "rgba(37,99,235,.12)", "#2563eb", "&#x26BD;"),
    "cosmetics": ("linear-gradient(135deg, #fdf2f8, #fbcfe8)", "rgba(236,72,153,.12)", "#ec4899", "&#x1F484;"),
    "geology": ("linear-gradient(135deg, #f5f5dc, #ddd6c1)", "rgba(120,113,108,.12)", "#78716c", "&#x1FAA8;"),
    "brewing": ("linear-gradient(135deg, #fef9c3, #fef08a)", "rgba(161,98,7,.12)", "#a16207", "&#x1F37A;"),
    "marine": ("linear-gradient(135deg, #cffafe, #67e8f9)", "rgba(6,182,212,.12)", "#0891b2", "&#x1F30A;"),
    "aviation": ("linear-gradient(135deg, #e0f2fe, #bae6fd)", "rgba(2,132,199,.12)", "#0284c7", "&#x2708;"),
    "electronics": ("linear-gradient(135deg, #ecfdf5, #a7f3d0)", "rgba(5,150,105,.12)", "#059669", "&#x1F50C;"),
    "painting": ("linear-gradient(135deg, #fef3c7, #fcd34d)", "rgba(217,119,6,.12)", "#d97706", "&#x1F3A8;"),
    "veterinary": ("linear-gradient(135deg, #fce7f3, #f9a8d4)", "rgba(219,39,119,.12)", "#db2777", "&#x1F404;"),
    "general": ("linear-gradient(135deg, #f1f5f9, #e2e8f0)", "rgba(71,85,105,.12)", "#475569", "&#x2699;"),
}

CATEGORIES = {
    27: "cloud", 28: "cloud", 29: "cloud", 30: "cloud", 31: "cloud", 32: "cloud", 33: "cloud", 34: "cloud", 36: "cloud",
    37: "data", 38: "data", 39: "data", 40: "data", 41: "data", 42: "data", 44: "data", 45: "data", 46: "data",
    47: "networking", 48: "networking", 49: "networking", 50: "networking", 51: "networking", 52: "networking", 54: "networking", 55: "networking", 56: "networking",
    57: "security", 58: "security", 59: "security", 60: "security", 61: "security", 62: "security", 63: "security", 64: "security", 65: "security",
    67: "iot", 68: "iot", 69: "iot", 70: "iot", 71: "iot", 72: "iot", 73: "iot", 74: "iot", 75: "iot", 76: "iot",
    77: "devops", 78: "devops", 79: "devops", 80: "devops", 81: "devops", 82: "devops", 83: "devops", 84: "devops", 86: "devops",
    87: "food", 88: "food", 89: "food", 91: "food", 93: "food", 95: "food", 96: "food",
    97: "agriculture", 98: "agriculture", 99: "agriculture", 100: "agriculture", 101: "agriculture", 102: "agriculture", 104: "agriculture", 105: "agriculture",
    107: "health", 108: "health", 109: "health", 110: "health", 111: "health", 113: "health", 114: "health",
    117: "automotive", 118: "automotive", 119: "automotive", 122: "automotive", 126: "automotive",
    127: "environment", 128: "environment", 129: "environment", 132: "environment", 135: "environment",
    137: "home", 138: "home", 139: "home", 140: "home", 141: "home", 144: "home", 146: "home",
    147: "photography", 148: "photography", 149: "photography", 151: "photography", 153: "photography", 154: "photography", 155: "photography",
    157: "music", 158: "music", 159: "music", 160: "music", 162: "music", 164: "music", 165: "music",
    167: "petcare", 168: "petcare", 169: "petcare", 170: "petcare", 171: "petcare", 173: "petcare", 174: "petcare",
    177: "textiles", 178: "textiles", 179: "textiles", 180: "textiles", 184: "textiles", 186: "textiles",
    187: "chemistry", 188: "chemistry", 190: "chemistry", 194: "chemistry", 195: "chemistry",
    197: "general", 198: "general", 249: "general", 250: "general",
    199: "woodworking", 200: "woodworking", 201: "woodworking", 202: "woodworking", 204: "woodworking", 205: "woodworking", 208: "woodworking",
    209: "sports", 210: "sports", 211: "sports", 212: "sports", 214: "sports", 218: "sports",
    219: "cosmetics", 220: "cosmetics", 221: "cosmetics", 222: "cosmetics", 224: "cosmetics", 226: "cosmetics",
    229: "geology", 230: "geology", 231: "geology", 232: "geology", 233: "geology", 234: "geology", 236: "geology",
    239: "brewing", 240: "brewing", 241: "brewing", 242: "brewing", 246: "brewing",
    251: "marine", 252: "marine", 253: "marine", 254: "marine", 256: "marine", 258: "marine",
    261: "aviation", 262: "aviation", 263: "aviation", 267: "aviation", 269: "aviation", 270: "aviation",
    271: "electronics", 272: "electronics", 274: "electronics", 275: "electronics", 277: "electronics", 278: "electronics", 280: "electronics",
    281: "painting", 282: "painting", 283: "painting", 284: "painting", 288: "painting",
    291: "veterinary", 292: "veterinary", 293: "veterinary", 294: "veterinary", 295: "veterinary", 297: "veterinary",
    301: "general", 302: "painting", 303: "chemistry", 304: "general",
    305: "cosmetics", 306: "general", 307: "brewing", 308: "electronics",
    309: "environment", 310: "electronics",
}

def slug_to_web(slug):
    return slug.replace("_", "-")

def escape(s):
    return html.escape(s).replace("°", "&deg;")

def get_analysis_output(num, config_path=None):
    path = f"/tmp/analyze_{num}.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    if config_path:
        try:
            result = subprocess.run(
                ["python", "doe.py", "analyze", "--config", config_path, "--no-plots"],
                capture_output=True, text=True, timeout=60,
            )
            return result.stdout
        except Exception as e:
            print(f"    Warning: analyze failed for {config_path}: {e}")
    return ""

def get_optimize_output(num, config_path=None):
    path = f"/tmp/optimize_{num}.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    if config_path:
        try:
            result = subprocess.run(
                ["python", "doe.py", "optimize", "--config", config_path],
                capture_output=True, text=True, timeout=60,
            )
            return result.stdout
        except Exception as e:
            print(f"    Warning: optimize failed for {config_path}: {e}")
    return ""

def get_multi_optimize_output(num, config_path=None, n_responses=1):
    """Run optimize --multi for use cases with 2+ responses."""
    if n_responses < 2:
        return ""
    path = f"/tmp/multi_optimize_{num}.txt"
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    if config_path:
        try:
            result = subprocess.run(
                ["python", "doe.py", "optimize", "--config", config_path, "--multi"],
                capture_output=True, text=True, timeout=60,
            )
            # Cache for reuse
            with open(path, "w") as f:
                f.write(result.stdout)
            return result.stdout
        except Exception as e:
            print(f"    Warning: multi optimize failed for {config_path}: {e}")
    return ""


def parse_multi_output(text):
    """Parse multi-objective optimization output into structured data."""
    if not text or "MULTI-OBJECTIVE OPTIMIZATION" not in text:
        return None

    result = {}

    # Overall desirability
    m = re.search(r"Overall desirability: D = ([0-9.]+)", text)
    result["overall_d"] = float(m.group(1)) if m else 0.0

    # Response table
    responses = []
    table_match = re.search(
        r"Response\s+Weight\s+Desirability\s+Predicted\s+Direction\n-+\n(.*?)(?:\n\n|\nRecommended)",
        text, re.DOTALL
    )
    if table_match:
        for line in table_match.group(1).strip().split("\n"):
            parts = line.split()
            if len(parts) >= 5:
                name = parts[0]
                weight = parts[1]
                desirability = parts[2]
                predicted = parts[3]
                # Unit may be embedded before direction arrow
                direction = "↑" if "↑" in line else "↓"
                # Extract unit: everything between predicted value and direction arrow
                unit_match = re.search(r"[0-9.]+\s+(.+?)\s+[↑↓]", line[25:])
                unit = unit_match.group(1).strip() if unit_match else ""
                responses.append({
                    "name": name,
                    "weight": weight,
                    "desirability": desirability,
                    "predicted": predicted,
                    "unit": unit,
                    "direction": direction,
                })
    result["responses"] = responses

    # Recommended settings
    settings = []
    settings_match = re.search(r"Recommended settings:\n(.*?)(?:\n\n|\nTrade-off)", text, re.DOTALL)
    if settings_match:
        for line in settings_match.group(1).strip().split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("("):
                parts = line.split("=", 1)
                settings.append((parts[0].strip(), parts[1].strip()))
            elif line.startswith("("):
                result["settings_source"] = line.strip("() ")
    result["settings"] = settings

    # Trade-off summary
    tradeoffs = []
    tradeoff_match = re.search(r"Trade-off summary:\n(.*?)(?:\n\n|\nModel quality)", text, re.DOTALL)
    if tradeoff_match:
        for line in tradeoff_match.group(1).strip().split("\n"):
            m = re.match(r"\s+(\S+):\s+([0-9.\-]+)\s+\(best observed:\s+([0-9.\-]+),\s+sacrifice:\s+([+\-0-9.]+)\)", line)
            if m:
                tradeoffs.append({
                    "name": m.group(1),
                    "predicted": m.group(2),
                    "best_observed": m.group(3),
                    "sacrifice": m.group(4),
                })
    result["tradeoffs"] = tradeoffs

    # Model quality
    models = []
    model_match = re.search(r"Model quality:\n(.*?)(?:\n\n|\nTop 3)", text, re.DOTALL)
    if model_match:
        for line in model_match.group(1).strip().split("\n"):
            m = re.match(r"\s+(\S+):\s+R²\s*=\s*([0-9.]+)\s+\((\w+)\)", line)
            if m:
                models.append({
                    "name": m.group(1),
                    "r_squared": m.group(2),
                    "model_type": m.group(3),
                })
    result["models"] = models

    # Top 3 runs
    top_runs = []
    top_match = re.search(r"Top 3 observed runs.*?:\n(.*?)$", text, re.DOTALL)
    if top_match:
        for line in top_match.group(1).strip().split("\n"):
            m = re.match(r"\s+(\d+)\.\s+Run #(\d+)\s+\(D=([0-9.]+)\):\s+(.*)", line)
            if m:
                top_runs.append({
                    "rank": m.group(1),
                    "run_id": m.group(2),
                    "d_value": m.group(3),
                    "factors": m.group(4),
                })
    result["top_runs"] = top_runs

    return result


def build_multi_objective_html(multi_data, multi_text):
    """Build an HTML section for multi-objective optimization results."""
    if not multi_data:
        return ""

    overall_d = multi_data["overall_d"]

    # Desirability score color
    if overall_d >= 0.8:
        d_color = "#16a34a"  # green
    elif overall_d >= 0.6:
        d_color = "#ca8a04"  # amber
    elif overall_d >= 0.4:
        d_color = "#ea580c"  # orange
    else:
        d_color = "#dc2626"  # red

    # Response desirability table
    resp_rows = ""
    for r in multi_data["responses"]:
        d_val = float(r["desirability"])
        if d_val >= 0.8:
            bar_color = "#22c55e"
        elif d_val >= 0.6:
            bar_color = "#eab308"
        elif d_val >= 0.4:
            bar_color = "#f97316"
        else:
            bar_color = "#ef4444"
        bar_width = max(2, d_val * 100)
        dir_html = f'<span style="color:{"#16a34a" if r["direction"] == "↑" else "#dc2626"}">{r["direction"]}</span>'
        unit_str = f' {escape(r["unit"])}' if r["unit"] else ""
        resp_rows += f'''            <tr>
              <td><code>{escape(r["name"])}</code></td>
              <td>{r["weight"]}</td>
              <td>
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:60px;height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden;">
                    <div style="width:{bar_width}%;height:100%;background:{bar_color};border-radius:4px;"></div>
                  </div>
                  <span>{r["desirability"]}</span>
                </div>
              </td>
              <td>{r["predicted"]}{unit_str}</td>
              <td>{dir_html}</td>
            </tr>
'''

    # Recommended settings
    settings_html = ""
    for name, val in multi_data["settings"]:
        settings_html += f"            <tr><td><code>{escape(name)}</code></td><td>{escape(val)}</td></tr>\n"
    source = multi_data.get("settings_source", "")
    source_html = f'<p style="font-size:.78rem;color:var(--faint);margin-top:8px;">Source: {escape(source)}</p>' if source else ""

    # Trade-off table
    tradeoff_rows = ""
    for t in multi_data["tradeoffs"]:
        sacrifice = t["sacrifice"]
        if sacrifice.startswith("+0.00") or sacrifice == "+0.00":
            sac_html = f'<span style="color:#16a34a;">{sacrifice}</span>'
        elif sacrifice.startswith("+"):
            sac_html = f'<span style="color:#dc2626;">{sacrifice}</span>'
        else:
            sac_html = f'<span style="color:#16a34a;">{sacrifice}</span>'
        tradeoff_rows += f'            <tr><td><code>{escape(t["name"])}</code></td><td>{t["predicted"]}</td><td>{t["best_observed"]}</td><td>{sac_html}</td></tr>\n'

    # Top 3 runs
    top_runs_html = ""
    for run in multi_data["top_runs"]:
        factors_formatted = run["factors"].replace(",", ", ")
        top_runs_html += f'            <tr><td>#{run["run_id"]}</td><td><strong>{run["d_value"]}</strong></td><td style="font-size:.78rem;">{escape(factors_formatted)}</td></tr>\n'

    # Model quality
    model_rows = ""
    for m in multi_data["models"]:
        r2 = float(m["r_squared"])
        if r2 >= 0.8:
            r2_color = "#16a34a"
        elif r2 >= 0.5:
            r2_color = "#ca8a04"
        else:
            r2_color = "#dc2626"
        model_rows += f'            <tr><td><code>{escape(m["name"])}</code></td><td style="color:{r2_color};font-weight:600;">{m["r_squared"]}</td><td>{m["model_type"]}</td></tr>\n'

    return f'''
  <!-- Multi-Objective Optimization -->
  <section class="uc-section">
    <h2>Multi-Objective Optimization</h2>
    <p>When responses compete, <strong>Derringer&ndash;Suich desirability</strong> finds the best compromise.
    Each response is scaled to a 0&ndash;1 desirability, then combined via a weighted geometric mean.</p>

    <div style="text-align:center;margin:20px 0;">
      <div style="display:inline-block;padding:16px 32px;border-radius:12px;background:linear-gradient(135deg,#f8fafc,#f1f5f9);border:2px solid {d_color};">
        <div style="font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.05em;">Overall Desirability</div>
        <div style="font-size:2.2rem;font-weight:800;color:{d_color};line-height:1.2;">D = {overall_d:.4f}</div>
      </div>
    </div>

    <h3>Per-Response Desirability</h3>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Response</th><th>Weight</th><th>Desirability</th><th>Predicted</th><th>Dir</th></tr></thead>
        <tbody>
{resp_rows}        </tbody>
      </table>
    </div>

    <h3>Recommended Settings</h3>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Factor</th><th>Value</th></tr></thead>
        <tbody>
{settings_html}        </tbody>
      </table>
    </div>
    {source_html}

    <h3>Trade-off Summary</h3>
    <p style="font-size:.85rem;color:var(--faint);">Sacrifice = how much worse than single-objective best.</p>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Response</th><th>Predicted</th><th>Best Observed</th><th>Sacrifice</th></tr></thead>
        <tbody>
{tradeoff_rows}        </tbody>
      </table>
    </div>

    <h3>Top 3 Runs by Desirability</h3>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Run</th><th>D</th><th>Factor Settings</th></tr></thead>
        <tbody>
{top_runs_html}        </tbody>
      </table>
    </div>

    <h3>Model Quality</h3>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Response</th><th>R&sup2;</th><th>Type</th></tr></thead>
        <tbody>
{model_rows}        </tbody>
      </table>
    </div>

    <h3>Full Multi-Objective Output</h3>
    <div class="code-block"><div class="code-header"><span>doe optimize --multi</span></div><div class="code-body" style="font-size:.72rem;line-height:1.5;">{escape(multi_text.strip())}</div></div>
  </section>
'''


def get_images(num):
    imgs = sorted(glob.glob(f"website/images/{num}_*.png"))
    return [os.path.basename(i) for i in imgs]

def parse_main_effects(text, response_name):
    pattern = rf"=== Main Effects: {re.escape(response_name)} ===(.*?)(?:=== |$)"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        lines = m.group(1).strip().split("\n")
        results = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 4 and parts[-1].endswith("%"):
                factor = parts[0]
                pct = parts[-1]
                results.append((factor, pct))
        return results
    return []

def parse_anova(text, response_name):
    """Extract ANOVA table from analyze output."""
    pattern = rf"=== ANOVA Table: {re.escape(response_name)} ===(.*?)(?:=== |$)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return []
    lines = m.group(1).strip().split("\n")
    rows = []
    for line in lines:
        if line.startswith("-") or line.startswith("  Note:"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            # Source may be multi-word (e.g., "Error (Lenth PSE)")
            # Try to parse from the right: p-value, F, MS, SS, DF, then source is the rest
            try:
                # Check if last columns are numeric
                source = parts[0]
                # Handle interaction terms like "A*B"
                if len(parts) >= 6:
                    rows.append({
                        "source": parts[0],
                        "df": parts[1],
                        "ss": parts[2],
                        "ms": parts[3],
                        "f": parts[4] if len(parts) > 4 else "",
                        "p": parts[5] if len(parts) > 5 else "",
                    })
                elif len(parts) >= 4:
                    rows.append({
                        "source": parts[0],
                        "df": parts[1],
                        "ss": parts[2],
                        "ms": parts[3],
                        "f": "",
                        "p": "",
                    })
            except (ValueError, IndexError):
                continue
    return rows


def parse_best_run(text, response_name):
    """Extract best observed run info from optimize output."""
    pattern = rf"=== Optimization: {re.escape(response_name)} ===.*?Best observed run: #(\d+)(.*?)(?:RSM Model|===|$)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return None, None
    run_num = m.group(1)
    block = m.group(2).strip()
    # Extract value
    val_match = re.search(r"Value:\s+([0-9.\-]+)", block)
    value = val_match.group(1) if val_match else None
    # Extract factor settings
    settings = []
    for line in block.split("\n"):
        line = line.strip()
        if "=" in line and "Value" not in line:
            parts = line.split("=", 1)
            settings.append((parts[0].strip(), parts[1].strip()))
    return value, settings


def build_summary_html(cfg, analyze_text, optimize_text, design_label, run_count):
    """Build a prose summary section from config and analysis data."""
    meta = cfg["metadata"]
    factors = cfg["factors"]
    responses = cfg["responses"]
    fixed = cfg.get("fixed_factors", {})
    design = cfg["settings"]["operation"]

    name = meta["name"]
    desc = meta["description"]
    n_factors = len(factors)
    n_responses = len(responses)

    # Build factor descriptions
    factor_parts = []
    for f in factors:
        unit_str = f" ({f.get('unit', '')})" if f.get("unit") else ""
        factor_parts.append(f"<strong>{f['name'].replace('_', ' ')}</strong>{unit_str}, ranging from {f['levels'][0]} to {f['levels'][-1]}")
    if len(factor_parts) == 1:
        factor_prose = factor_parts[0]
    elif len(factor_parts) == 2:
        factor_prose = " and ".join(factor_parts)
    else:
        factor_prose = ", ".join(factor_parts[:-1]) + ", and " + factor_parts[-1]

    # Build response descriptions
    resp_parts = []
    for r in responses:
        direction = "maximize" if r.get("optimize", "maximize") == "maximize" else "minimize"
        unit_str = f" ({r.get('unit', '')})" if r.get("unit") else ""
        resp_parts.append(f"{r['name'].replace('_', ' ')}{unit_str} ({direction})")
    resp_prose = " and ".join(resp_parts) if len(resp_parts) <= 2 else ", ".join(resp_parts[:-1]) + ", and " + resp_parts[-1]

    # Fixed factors
    fixed_prose = ""
    if fixed:
        fixed_items = [f"{k.replace('_', ' ')} = {v}" for k, v in fixed.items()]
        fixed_prose = f" Fixed conditions held constant across all runs include {', '.join(fixed_items)}."

    # Design rationale
    design_notes = {
        "box_behnken": f"A Box-Behnken design was chosen because it efficiently fits quadratic models with {n_factors} continuous factors while avoiding extreme corner combinations &mdash; requiring only {run_count} runs instead of the {2**n_factors} needed for a full factorial at two levels.",
        "central_composite": f"A Central Composite Design (CCD) was selected to fit a full quadratic response surface model, including curvature and interaction effects. With {n_factors} factors this produces {run_count} runs including center points and axial (star) points that extend beyond the factorial range.",
        "full_factorial": f"A full factorial design was used to explore all {2**n_factors} possible combinations of the {n_factors} factors at two levels. This guarantees that every main effect and interaction can be estimated independently, at the cost of a larger experiment ({run_count} runs).",
        "fractional_factorial": f"A fractional factorial design reduces the number of runs from {2**n_factors} to {run_count} by deliberately confounding higher-order interactions. This is ideal for screening &mdash; identifying which of the {n_factors} factors matter most before investing in a full study.",
        "plackett_burman": f"A Plackett-Burman screening design was used to efficiently test {n_factors} factors in only {run_count} runs. This design assumes interactions are negligible and focuses on identifying the most influential main effects.",
        "latin_hypercube": f"Latin Hypercube Sampling was used to space {run_count} runs across the {n_factors}-dimensional factor space with good coverage and minimal gaps, making it ideal for computer experiments where the response surface may be complex.",
    }
    design_prose = design_notes.get(design, f"The {design_label} produces {run_count} experimental runs.")

    # Parse results
    results_prose = ""
    next_steps = []
    for r in responses:
        rname = r["name"]
        effects = parse_main_effects(analyze_text, rname)
        best_val, best_settings = parse_best_run(optimize_text, rname)

        if effects:
            top_factors = effects[:3]
            top_str = ", ".join(f"{f.replace('_', ' ')} ({p})" for f, p in top_factors)
            results_prose += f"<p>For <strong>{rname.replace('_', ' ')}</strong>, the most influential factors were {top_str}."
            if best_val:
                results_prose += f" The best observed value was <strong>{best_val}</strong>"
                if best_settings:
                    settings_str = ", ".join(f"{k.replace('_', ' ')} = {v}" for k, v in best_settings[:3])
                    results_prose += f" (at {settings_str})"
                results_prose += "."
            results_prose += "</p>\n"

    # Determine if there are interactions or curvature worth noting
    has_rsm = "RSM Model (quadratic" in optimize_text
    has_curvature = "significant curvature" in optimize_text.lower() or "saddle" in optimize_text.lower()

    special_notes = ""
    if has_curvature:
        special_notes = "<p>The quadratic RSM model detected significant curvature in the response surface, indicating that optimal settings lie within the interior of the design space rather than at the extremes. The contour plots below show these nonlinear relationships.</p>\n"
    elif has_rsm:
        special_notes = "<p>Quadratic response surface models were fitted to capture potential curvature and factor interactions. The RSM contour plots below visualize how pairs of factors jointly affect each response.</p>\n"

    # Next steps
    if design in ("plackett_burman", "fractional_factorial"):
        next_steps.append("Follow up with a response surface design (CCD or Box-Behnken) on the top 3&ndash;4 factors to model curvature and find the true optimum.")
    if design in ("box_behnken", "central_composite"):
        next_steps.append("Run confirmation experiments at the predicted optimal settings to validate the model.")
    next_steps.append("Consider whether any fixed factors should be varied in a future study.")
    if n_factors >= 5:
        next_steps.append("The screening results can guide factor reduction &mdash; drop factors contributing less than 5% and re-run with a smaller, more focused design.")

    next_html = "<ul>\n" + "".join(f"    <li>{s}</li>\n" for s in next_steps) + "  </ul>"

    summary = f'''
  <!-- Prose Summary -->
  <section class="uc-section">
    <h2>Summary</h2>
    <p>This experiment investigates <strong>{escape(name.lower())}</strong>. {escape(desc)}.</p>

    <p>The design varies {n_factors} factors: {factor_prose}. The goal is to optimize {n_responses} response{"s" if n_responses > 1 else ""}: {resp_prose}.{fixed_prose}</p>

    <p>{design_prose}</p>

    {special_notes}
    <h3>Key Findings</h3>
    {results_prose if results_prose else "<p>Run the analysis to see detailed results.</p>"}

    <h3>Recommended Next Steps</h3>
    {next_html}
  </section>
'''
    return summary


def build_matrix_html(config_path, design_label, seed=42):
    """Generate the experimental matrix HTML section from a config file."""
    try:
        cfg = load_config(config_path, strict=False)
        matrix = generate_design(cfg, seed=seed)
    except Exception as e:
        print(f"    Warning: could not generate matrix for {config_path}: {e}")
        return ""

    runs = matrix.runs
    factor_names = matrix.factor_names
    n_runs = len(runs)
    has_blocks = any(r.block_id != runs[0].block_id for r in runs) if runs else False

    # Build header
    header_cells = "<th>Run</th>"
    if has_blocks:
        header_cells += "<th>Block</th>"
    for fname in factor_names:
        header_cells += f"<th><code>{escape(fname)}</code></th>"

    # Build rows
    body_rows = ""
    for run in runs:
        row = f"<td>{run.run_id}</td>"
        if has_blocks:
            row += f"<td>{run.block_id}</td>"
        for fname in factor_names:
            val = run.factor_values.get(fname, "")
            row += f"<td>{escape(val)}</td>"
        body_rows += f"        <tr>{row}</tr>\n"

    return f'''
  <!-- Experimental Matrix -->
  <section class="uc-section">
    <h2>Experimental Matrix</h2>
    <p>The {design_label} produces <strong>{n_runs} runs</strong>. Each row is one experiment with specific factor settings.</p>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr>{header_cells}</tr></thead>
        <tbody>
{body_rows}        </tbody>
      </table>
    </div>
  </section>
'''


def build_page(num, uc_dir):
    config_path = os.path.join(uc_dir, "config.json")
    with open(config_path) as f:
        cfg = json.load(f)

    meta = cfg["metadata"]
    factors = cfg["factors"]
    responses = cfg["responses"]
    fixed = cfg.get("fixed_factors", {})
    design = cfg["settings"]["operation"]
    design_label = DESIGN_LABELS.get(design, design)
    cat = CATEGORIES[num]
    hero_bg, badge_bg, badge_color, hero_icon = HERO_STYLES[cat]

    slug = os.path.basename(uc_dir).split("_", 1)[1]
    web_slug = slug_to_web(slug)
    web_file = f"{num:02d}-{web_slug}.html"

    run_count = len(glob.glob(os.path.join(uc_dir, "results", "run_*.json")))

    analyze_text = get_analysis_output(num, config_path)
    optimize_text = get_optimize_output(num, config_path)
    multi_text = get_multi_optimize_output(num, config_path, len(responses))
    multi_data = parse_multi_output(multi_text)
    images = get_images(num)

    pareto_imgs = [i for i in images if "pareto_" in i]
    main_effect_imgs = [i for i in images if "main_effects_" in i]
    rsm_imgs = [i for i in images if "rsm_" in i]
    half_normal_imgs = [i for i in images if "half_normal_effects_" in i]
    normal_imgs = [i for i in images if "normal_effects_" in i and "half_normal_effects_" not in i]
    diagnostics_imgs = [i for i in images if "diagnostics_" in i]

    factor_rows = ""
    for f in factors:
        low, high = f["levels"][0], f["levels"][-1]
        unit = escape(f.get("unit", ""))
        factor_rows += f'            <tr><td><code>{escape(f["name"])}</code></td><td>{escape(low)}</td><td>{escape(high)}</td><td>{unit}</td></tr>\n'

    fixed_str = ", ".join(f'{k} = {v}' for k, v in fixed.items())

    resp_rows = ""
    for r in responses:
        direction = r.get("optimize", "maximize")
        if direction == "maximize":
            dir_html = '<td style="color:var(--mint);font-weight:600;">&#x2191; maximize</td>'
        else:
            dir_html = '<td style="color:var(--coral);font-weight:600;">&#x2193; minimize</td>'
        unit = escape(r.get("unit", ""))
        resp_rows += f'            <tr><td><code>{escape(r["name"])}</code></td>{dir_html}<td>{unit}</td></tr>\n'

    config_display = json.dumps({
        "metadata": {"name": meta["name"], "description": meta["description"]},
        "factors": [{"name": f["name"], "levels": f["levels"], "type": f["type"], "unit": f.get("unit", "")} for f in factors],
        "fixed_factors": fixed,
        "responses": [{"name": r["name"], "optimize": r.get("optimize", "maximize"), "unit": r.get("unit", "")} for r in responses],
        "settings": {"operation": design, "test_script": f"doe/use_cases/{num:02d}_{slug}/sim.sh"}
    }, indent=2)

    config_html = escape(config_display)
    config_html = re.sub(r'"([^"]+)":', r'<span class="key">"\1"</span>:', config_html)
    config_html = re.sub(r': "([^"]*)"', r': <span class="string">"\1"</span>', config_html)

    matrix_html = build_matrix_html(config_path, design_label)

    summary_html = build_summary_html(cfg, analyze_text, optimize_text, design_label, run_count)

    analysis_html = ""
    for r in responses:
        rname = r["name"]
        effects = parse_main_effects(analyze_text, rname)
        if effects:
            effect_desc = ", ".join(f"{f} ({p})" for f, p in effects[:3])
            analysis_html += f'\n    <h3>Response: {escape(rname)}</h3>\n'
            analysis_html += f'    <p>Top factors: {effect_desc}.</p>\n'
        else:
            analysis_html += f'\n    <h3>Response: {escape(rname)}</h3>\n'

        # ANOVA table
        anova_rows = parse_anova(analyze_text, rname)
        if anova_rows:
            analysis_html += '    <h4>ANOVA</h4>\n'
            analysis_html += '    <table style="font-size:.82rem;">\n'
            analysis_html += '      <thead><tr><th>Source</th><th>DF</th><th>SS</th><th>MS</th><th>F</th><th>p-value</th></tr></thead>\n'
            analysis_html += '      <tbody>\n'
            for row in anova_rows:
                p_val = row.get("p", "")
                # Highlight significant terms
                style = ""
                try:
                    if p_val and float(p_val) < 0.05:
                        style = ' style="font-weight:600;color:var(--mint);"'
                except ValueError:
                    pass
                analysis_html += f'        <tr{style}><td>{escape(row["source"])}</td><td>{row["df"]}</td><td>{row["ss"]}</td><td>{row["ms"]}</td><td>{row["f"]}</td><td>{p_val}</td></tr>\n'
            analysis_html += '      </tbody>\n    </table>\n'

        pareto = [i for i in pareto_imgs if rname in i]
        me = [i for i in main_effect_imgs if rname in i]
        normal = [i for i in normal_imgs if rname in i]
        half_normal = [i for i in half_normal_imgs if rname in i]
        diag = [i for i in diagnostics_imgs if rname in i]

        if pareto or me:
            analysis_html += '    <div class="results-grid">\n'
            for img in pareto:
                analysis_html += f'      <div>\n        <p class="caption">Pareto Chart</p>\n        <img src="../images/{img}" alt="Pareto chart for {escape(rname)}">\n      </div>\n'
            for img in me:
                analysis_html += f'      <div>\n        <p class="caption">Main Effects Plot</p>\n        <img src="../images/{img}" alt="Main effects plot for {escape(rname)}">\n      </div>\n'
            analysis_html += '    </div>\n'

        if normal or half_normal:
            analysis_html += '    <div class="results-grid">\n'
            for img in normal:
                analysis_html += f'      <div>\n        <p class="caption">Normal Probability Plot of Effects</p>\n        <img src="../images/{img}" alt="Normal probability plot for {escape(rname)}">\n      </div>\n'
            for img in half_normal:
                analysis_html += f'      <div>\n        <p class="caption">Half-Normal Plot of Effects</p>\n        <img src="../images/{img}" alt="Half-normal plot for {escape(rname)}">\n      </div>\n'
            analysis_html += '    </div>\n'

        if diag:
            analysis_html += '    <div class="results-grid">\n'
            for img in diag:
                analysis_html += f'      <div>\n        <p class="caption">Model Diagnostics</p>\n        <img src="../images/{img}" alt="Model diagnostics for {escape(rname)}">\n      </div>\n'
            analysis_html += '    </div>\n'

    rsm_html = ""
    if rsm_imgs:
        rsm_html = '\n  <section class="uc-section">\n    <h2>Response Surface Plots</h2>\n    <p>3D surfaces fitted with quadratic RSM. Red dots are observed data points.</p>\n'
        for img in rsm_imgs:
            parts = img.replace(".png", "").split("_", 2)
            if len(parts) >= 3:
                rest = parts[2]
                label = rest.replace("_vs_", " vs ").replace("_", " ")
            else:
                label = img
            rsm_html += f'\n    <div style="margin:20px 0;">\n      <p style="font-size:.78rem;color:var(--faint);margin-bottom:4px;">{label}</p>\n      <img src="../images/{img}" alt="RSM surface: {label}" style="width:100%;max-width:700px;border-radius:8px;border:1px solid var(--border);">\n    </div>\n'
        rsm_html += '  </section>\n'

    multi_objective_html = build_multi_objective_html(multi_data, multi_text)

    multi_step_html = ""
    if len(responses) >= 2:
        multi_step_html = f'''
    <div class="uc-step">
      <div class="uc-step-num">6</div>
      <div class="uc-step-body">
        <h3>Multi-objective optimization</h3>
        <p>With {len(responses)} competing responses, use <code>--multi</code> to find the best compromise via Derringer&ndash;Suich desirability.</p>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe optimize <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json <span class="flag">--multi</span></div>
        </div>
      </div>
    </div>
'''

    cont_count = sum(1 for f in factors if f["type"] == "continuous")
    cat_count = sum(1 for f in factors if f["type"] == "categorical")
    if cat_count > 0:
        factor_type_str = f'<code>continuous</code> ({cont_count}), <code>categorical</code> ({cat_count})'
    else:
        factor_type_str = f'<code>continuous</code> (all {cont_count})'

    resp_summary = ", ".join(
        f'{r["name"]} {"&#x2191;" if r.get("optimize","maximize")=="maximize" else "&#x2193;"}'
        for r in responses
    )

    prev_num = num - 1
    next_num = num + 1
    prev_link = ""
    next_link = ""

    if prev_num >= 1:
        prev_dirs = glob.glob(f"doe/use_cases/{prev_num:02d}_*")
        if prev_dirs:
            prev_slug = os.path.basename(prev_dirs[0]).split("_", 1)[1]
            prev_web = slug_to_web(prev_slug)
            prev_cfg = json.load(open(os.path.join(prev_dirs[0], "config.json")))
            prev_name = prev_cfg["metadata"]["name"]
            prev_link = f'<a href="{prev_num:02d}-{prev_web}.html">&larr; Previous: {escape(prev_name)}</a>'

    if next_num <= 310:
        next_dirs = glob.glob(f"doe/use_cases/{next_num:02d}_*")
        if next_dirs:
            next_slug = os.path.basename(next_dirs[0]).split("_", 1)[1]
            next_web = slug_to_web(next_slug)
            next_cfg = json.load(open(os.path.join(next_dirs[0], "config.json")))
            next_name = next_cfg["metadata"]["name"]
            next_link = f'<a href="{next_num:02d}-{next_web}.html">Next: {escape(next_name)} &rarr;</a>'

    if not prev_link:
        prev_link = '<a href="index.html">&larr; All Use Cases</a>'
    if not next_link:
        next_link = '<a href="index.html">All Use Cases &rarr;</a>'

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(meta["name"])} &mdash; DOE Use Case</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/usecase.css">
</head>
<body>

<nav class="nav scrolled">
  <div class="nav-inner">
    <a href="../index.html" class="nav-logo"><img src="../logo.svg" alt="" class="nav-logo-icon"> doe-helper</a>
    <ul class="nav-links">
      <li><a href="../index.html">Home</a></li>
      <li><a href="../howto.html">Quick Start</a></li>
      <li><a href="index.html">Use Cases</a></li>
      <li><a href="../book.html" class="cta">Guide</a></li>
    </ul>
    <button class="nav-toggle" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</nav>

<!-- Hero -->
<section class="uc-hero-detail" style="background: {hero_bg};">
  <div class="container-narrow">
    <a href="index.html" class="uc-back">&larr; All Use Cases</a>
    <div class="uc-hero-icon">{hero_icon}</div>
    <div class="uc-badge" style="background:{badge_bg};color:{badge_color};">{design_label}</div>
    <h1>{escape(meta["name"])}</h1>
    <p class="uc-subtitle">{escape(meta["description"])}</p>
  </div>
</section>

<!-- Table of Contents -->
<nav class="uc-toc" id="uc-toc"><div class="uc-toc-inner" id="uc-toc-inner"></div></nav>

<div class="container-narrow uc-content">

{summary_html}
  <!-- Factors & Responses -->
  <section class="uc-section">
    <h2>Experimental Setup</h2>
    <div class="uc-tables-grid">
      <div>
        <h3>Factors</h3>
        <table>
          <thead><tr><th>Factor</th><th>Low</th><th>High</th><th>Unit</th></tr></thead>
          <tbody>
{factor_rows}          </tbody>
        </table>
        <p class="uc-fixed"><strong>Fixed:</strong> {escape(fixed_str)}</p>
      </div>
      <div>
        <h3>Responses</h3>
        <table>
          <thead><tr><th>Response</th><th>Direction</th><th>Unit</th></tr></thead>
          <tbody>
{resp_rows}          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- Config -->
  <section class="uc-section">
    <h2>Configuration</h2>
    <div class="code-block">
      <div class="code-header"><span>use_cases/{num:02d}_{slug}/config.json</span><button class="code-copy">Copy</button></div>
      <div class="code-body">{config_html}</div>
    </div>
  </section>

{matrix_html}
  <!-- Workflow -->
  <section class="uc-section">
    <h2>Step-by-Step Workflow</h2>

    <div class="uc-step">
      <div class="uc-step-num">1</div>
      <div class="uc-step-body">
        <h3>Preview the design</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe info <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">2</div>
      <div class="uc-step-body">
        <h3>Generate the runner script</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe generate <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json \\
    <span class="flag">--output</span> use_cases/{num:02d}_{slug}/results/run.sh <span class="flag">--seed</span> 42</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">3</div>
      <div class="uc-step-body">
        <h3>Execute the experiments</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>bash use_cases/{num:02d}_{slug}/results/run.sh</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">4</div>
      <div class="uc-step-body">
        <h3>Analyze results</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe analyze <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">5</div>
      <div class="uc-step-body">
        <h3>Get optimization recommendations</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe optimize <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>
{multi_step_html}
    <div class="uc-step">
      <div class="uc-step-num">{"7" if len(responses) >= 2 else "6"}</div>
      <div class="uc-step-body">
        <h3>Generate the HTML report</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>doe report <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json \\
    <span class="flag">--output</span> use_cases/{num:02d}_{slug}/results/report.html</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Features -->
  <section class="uc-section">
    <h2>Features Exercised</h2>
    <table>
      <thead><tr><th>Feature</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Design type</td><td><code>{design}</code></td></tr>
        <tr><td>Factor types</td><td>{factor_type_str}</td></tr>
        <tr><td>Arg style</td><td><code>double-dash</code></td></tr>
        <tr><td>Responses</td><td>{len(responses)} ({resp_summary})</td></tr>
        <tr><td>Total runs</td><td>{run_count}</td></tr>
      </tbody>
    </table>
  </section>

  <style>
    .results-grid {{ display:grid; grid-template-columns:1fr; gap:16px; margin:16px 0; }}
    @media (max-width:700px) {{ .results-grid {{ grid-template-columns:1fr; }} }}
    .results-grid img {{ width:100%; border-radius:8px; border:1px solid var(--border); }}
    .results-grid .caption {{ font-size:.75rem; color:var(--faint); margin-bottom:6px; }}
  </style>

  <section class="uc-section">
    <h2>Analysis Results</h2>
    <p>Generated from actual experiment runs using the DOE Helper Tool.</p>
{analysis_html}
  </section>

{rsm_html}

{multi_objective_html}

  <section class="uc-section">
    <h3>Full Analysis Output</h3>
    <div class="code-block"><div class="code-header"><span>doe analyze</span></div><div class="code-body" style="font-size:.72rem;line-height:1.5;">{escape(analyze_text.strip())}</div></div>

    <h3>Optimization Recommendations</h3>
    <div class="code-block"><div class="code-header"><span>doe optimize</span></div><div class="code-body" style="font-size:.72rem;line-height:1.5;">{escape(optimize_text.strip())}</div></div>
  </section>

  <!-- Nav -->
  <div class="chapter-nav">
    {prev_link}
    {next_link}
  </div>
</div>

<footer class="footer">
  <div class="container"><div class="footer-inner"><span class="mono" style="font-size:.78rem;">doe-helper &middot; Created by Martin J. Gallagher for <a href="https://sagecor.com/" style="margin:0;color:inherit;text-decoration:underline;">SageCor Solutions</a> &middot; GPL-3.0 &middot; 2025</span></div></div>
</footer>
<script src="../js/main.js"></script>
<script>
(function() {{
  var toc = document.getElementById('uc-toc-inner');
  if (!toc) return;
  var headings = document.querySelectorAll('.uc-section > h2, .uc-content > section > h2');
  if (headings.length < 2) {{ document.getElementById('uc-toc').style.display = 'none'; return; }}
  headings.forEach(function(h, i) {{
    if (!h.id) h.id = 'sec-' + i;
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    a.addEventListener('click', function(e) {{
      e.preventDefault();
      h.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      history.replaceState(null, '', '#' + h.id);
    }});
    toc.appendChild(a);
  }});
  var links = toc.querySelectorAll('a');
  var observer = new IntersectionObserver(function(entries) {{
    entries.forEach(function(entry) {{
      if (entry.isIntersecting) {{
        links.forEach(function(a) {{ a.classList.remove('active'); }});
        var active = toc.querySelector('a[href="#' + entry.target.id + '"]');
        if (active) {{
          active.classList.add('active');
          active.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
        }}
      }}
    }});
  }}, {{ rootMargin: '-80px 0px -70% 0px', threshold: 0 }});
  headings.forEach(function(h) {{ observer.observe(h); }});
  if (links.length) links[0].classList.add('active');
}})();
</script>
</body>
</html>'''

    out_path = os.path.join("website", "use-cases", web_file)
    with open(out_path, "w") as f:
        f.write(page)
    print(f"  [{num:02d}] {web_file} ({len(page)//1024}KB)")


def inject_matrix_into_existing(num, uc_dir):
    """Inject experimental matrix into an existing hand-crafted HTML page (use cases 1-26)."""
    config_path = os.path.join(uc_dir, "config.json")
    if not os.path.exists(config_path):
        print(f"  [{num:02d}] skipped (no config.json)")
        return

    with open(config_path) as f:
        cfg = json.load(f)
    design = cfg["settings"]["operation"]
    design_label = DESIGN_LABELS.get(design, design)

    matrix_html = build_matrix_html(config_path, design_label)

    responses = cfg["responses"]

    # Build summary
    analyze_text = get_analysis_output(num, config_path)
    optimize_text = get_optimize_output(num, config_path)
    multi_text = get_multi_optimize_output(num, config_path, len(responses))
    multi_data = parse_multi_output(multi_text)
    run_count = len(glob.glob(os.path.join(uc_dir, "results", "run_*.json")))
    summary_html = build_summary_html(cfg, analyze_text, optimize_text, design_label, run_count)
    multi_html = build_multi_objective_html(multi_data, multi_text)

    slug = os.path.basename(uc_dir).split("_", 1)[1]
    web_slug = slug_to_web(slug)
    html_path = os.path.join("website", "use-cases", f"{num:02d}-{web_slug}.html")

    if not os.path.exists(html_path):
        # Try finding any matching HTML file
        candidates = glob.glob(os.path.join("website", "use-cases", f"{num:02d}-*.html"))
        if candidates:
            html_path = candidates[0]
        else:
            print(f"  [{num:02d}] skipped (no HTML file found)")
            return

    with open(html_path) as f:
        page = f.read()

    # Remove any previously injected sections
    page = re.sub(
        r'\n  <!-- Experimental Matrix -->.*?</section>\n',
        '',
        page,
        flags=re.DOTALL,
    )
    page = re.sub(
        r'\n  <!-- Prose Summary -->.*?</section>\n',
        '',
        page,
        flags=re.DOTALL,
    )
    page = re.sub(
        r'\n  <!-- Multi-Objective Optimization -->.*?</section>\n',
        '',
        page,
        flags=re.DOTALL,
    )

    # Insert summary after container-narrow uc-content
    if 'class="container-narrow uc-content"' in page:
        page = page.replace(
            'class="container-narrow uc-content">',
            f'class="container-narrow uc-content">\n{summary_html}',
        )
    elif '<!-- Scenario -->' in page:
        page = page.replace(
            '  <!-- Scenario -->',
            f'{summary_html}\n  <!-- Scenario -->',
        )

    # Insert matrix before the Workflow section — try comment marker first, then h2 text
    if "<!-- Workflow -->" in page:
        page = page.replace(
            "  <!-- Workflow -->",
            f"{matrix_html}\n  <!-- Workflow -->",
        )
    elif '<h2>Step-by-Step Workflow</h2>' in page:
        page = re.sub(
            r'(  <section class="uc-section">\s*\n\s*<h2>Step-by-Step Workflow</h2>)',
            f'{matrix_html}\n\\1',
            page,
            count=1,
        )
    elif '<h2>How to Run</h2>' in page:
        page = re.sub(
            r'(  <section class="uc-section">\s*\n\s*<h2>How to Run</h2>)',
            f'{matrix_html}\n\\1',
            page,
            count=1,
        )
    else:
        print(f"  [{num:02d}] skipped (no Workflow/How to Run section found)")
        return

    # Inject multi-objective HTML before the chapter-nav or footer
    if multi_html:
        if '<div class="chapter-nav">' in page:
            page = page.replace(
                '<div class="chapter-nav">',
                f'{multi_html}\n  <div class="chapter-nav">',
            )
        elif '<footer' in page:
            page = page.replace(
                '<footer',
                f'{multi_html}\n<footer',
            )

    # Inject TOC nav if not already present
    toc_nav = '<!-- Table of Contents -->\n<nav class="uc-toc" id="uc-toc"><div class="uc-toc-inner" id="uc-toc-inner"></div></nav>'
    toc_script = """<script>
(function() {
  var toc = document.getElementById('uc-toc-inner');
  if (!toc) return;
  var headings = document.querySelectorAll('.uc-section > h2, .uc-content > section > h2');
  if (headings.length < 2) { document.getElementById('uc-toc').style.display = 'none'; return; }
  headings.forEach(function(h, i) {
    if (!h.id) h.id = 'sec-' + i;
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    a.addEventListener('click', function(e) {
      e.preventDefault();
      h.scrollIntoView({ behavior: 'smooth', block: 'start' });
      history.replaceState(null, '', '#' + h.id);
    });
    toc.appendChild(a);
  });
  var links = toc.querySelectorAll('a');
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        links.forEach(function(a) { a.classList.remove('active'); });
        var active = toc.querySelector('a[href="#' + entry.target.id + '"]');
        if (active) {
          active.classList.add('active');
          active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
        }
      }
    });
  }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });
  headings.forEach(function(h) { observer.observe(h); });
  if (links.length) links[0].classList.add('active');
})();
</script>"""

    # Remove old TOC if present
    page = re.sub(r'\n<!-- Table of Contents -->\n<nav class="uc-toc"[^>]*>.*?</nav>\n', '\n', page, flags=re.DOTALL)
    page = re.sub(r'<script>\n\(function\(\) \{\n  var toc = document\.getElementById.*?\n</script>', '', page, flags=re.DOTALL)

    # Insert TOC nav after hero section
    if 'id="uc-toc"' not in page:
        # Match the hero closing + content div with flexible whitespace
        toc_inserted = re.sub(
            r'(</section>\s*)\n(\s*<div class="container-narrow uc-content">)',
            rf'\1\n{toc_nav}\n\n\2',
            page,
            count=1,
        )
        if toc_inserted != page:
            page = toc_inserted

    # Insert TOC script before </body>
    if '</body>' in page and 'var toc = document.getElementById' not in page:
        page = page.replace('</body>', f'{toc_script}\n</body>')

    with open(html_path, "w") as f:
        f.write(page)
    print(f"  [{num:02d}] injected matrix into {os.path.basename(html_path)}")


def main():
    # Generate pages for use cases 27-300
    for num in range(27, 311):
        pattern = f"doe/use_cases/{num:02d}_*" if num < 100 else f"doe/use_cases/{num}_*"
        dirs = glob.glob(pattern)
        if dirs:
            build_page(num, dirs[0])
    print(f"\n  HTML pages generated (27-300, skipping removed use cases).")

    # Inject experimental matrix into existing pages for use cases 1-26
    print("\nInjecting experimental matrices into use cases 1-26...")
    for num in range(1, 27):
        dirs = glob.glob(f"doe/use_cases/{num:02d}_*")
        if dirs:
            inject_matrix_into_existing(num, dirs[0])
    print(f"\nDone: all use case pages updated with experimental matrices.")


if __name__ == "__main__":
    main()
