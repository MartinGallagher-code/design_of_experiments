#!/usr/bin/env python3
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
    27: "cloud", 28: "cloud", 29: "cloud", 30: "cloud", 31: "cloud",
    32: "cloud", 33: "cloud", 34: "cloud", 35: "cloud", 36: "cloud",
    37: "data", 38: "data", 39: "data", 40: "data", 41: "data",
    42: "data", 43: "data", 44: "data", 45: "data", 46: "data",
    47: "networking", 48: "networking", 49: "networking", 50: "networking",
    51: "networking", 52: "networking", 53: "networking", 54: "networking",
    55: "networking", 56: "networking",
    57: "security", 58: "security", 59: "security", 60: "security", 61: "security",
    62: "security", 63: "security", 64: "security", 65: "security", 66: "security",
    67: "iot", 68: "iot", 69: "iot", 70: "iot", 71: "iot",
    72: "iot", 73: "iot", 74: "iot", 75: "iot", 76: "iot",
    77: "devops", 78: "devops", 79: "devops", 80: "devops", 81: "devops",
    82: "devops", 83: "devops", 84: "devops", 85: "devops", 86: "devops",
    87: "food", 88: "food", 89: "food", 90: "food", 91: "food",
    92: "food", 93: "food", 94: "food", 95: "food", 96: "food",
    97: "agriculture", 98: "agriculture", 99: "agriculture", 100: "agriculture",
    101: "agriculture", 102: "agriculture", 103: "agriculture", 104: "agriculture",
    105: "agriculture", 106: "agriculture",
    107: "health", 108: "health", 109: "health", 110: "health", 111: "health",
    112: "health", 113: "health", 114: "health", 115: "health", 116: "health",
    117: "automotive", 118: "automotive", 119: "automotive", 120: "automotive",
    121: "automotive", 122: "automotive", 123: "automotive", 124: "automotive",
    125: "automotive", 126: "automotive",
    127: "environment", 128: "environment", 129: "environment", 130: "environment",
    131: "environment", 132: "environment", 133: "environment", 134: "environment",
    135: "environment", 136: "environment",
    137: "home", 138: "home", 139: "home", 140: "home", 141: "home",
    142: "home", 143: "home", 144: "home", 145: "home", 146: "home",
    147: "photography", 148: "photography", 149: "photography", 150: "photography",
    151: "photography", 152: "photography", 153: "photography", 154: "photography",
    155: "photography", 156: "photography",
    157: "music", 158: "music", 159: "music", 160: "music", 161: "music",
    162: "music", 163: "music", 164: "music", 165: "music", 166: "music",
    167: "petcare", 168: "petcare", 169: "petcare", 170: "petcare", 171: "petcare",
    172: "petcare", 173: "petcare", 174: "petcare", 175: "petcare", 176: "petcare",
    177: "textiles", 178: "textiles", 179: "textiles", 180: "textiles", 181: "textiles",
    182: "textiles", 183: "textiles", 184: "textiles", 185: "textiles", 186: "textiles",
    187: "chemistry", 188: "chemistry", 189: "chemistry", 190: "chemistry", 191: "chemistry",
    192: "chemistry", 193: "chemistry", 194: "chemistry", 195: "chemistry", 196: "chemistry",
    197: "general", 198: "general",
    199: "woodworking", 200: "woodworking", 201: "woodworking", 202: "woodworking",
    203: "woodworking", 204: "woodworking", 205: "woodworking", 206: "woodworking",
    207: "woodworking", 208: "woodworking",
    209: "sports", 210: "sports", 211: "sports", 212: "sports", 213: "sports",
    214: "sports", 215: "sports", 216: "sports", 217: "sports", 218: "sports",
    219: "cosmetics", 220: "cosmetics", 221: "cosmetics", 222: "cosmetics", 223: "cosmetics",
    224: "cosmetics", 225: "cosmetics", 226: "cosmetics", 227: "cosmetics", 228: "cosmetics",
    229: "geology", 230: "geology", 231: "geology", 232: "geology", 233: "geology",
    234: "geology", 235: "geology", 236: "geology", 237: "geology", 238: "geology",
    239: "brewing", 240: "brewing", 241: "brewing", 242: "brewing", 243: "brewing",
    244: "brewing", 245: "brewing", 246: "brewing", 247: "brewing", 248: "brewing",
    249: "general", 250: "general",
    251: "marine", 252: "marine", 253: "marine", 254: "marine", 255: "marine",
    256: "marine", 257: "marine", 258: "marine", 259: "marine", 260: "marine",
    261: "aviation", 262: "aviation", 263: "aviation", 264: "aviation", 265: "aviation",
    266: "aviation", 267: "aviation", 268: "aviation", 269: "aviation", 270: "aviation",
    271: "electronics", 272: "electronics", 273: "electronics", 274: "electronics",
    275: "electronics", 276: "electronics", 277: "electronics", 278: "electronics",
    279: "electronics", 280: "electronics",
    281: "painting", 282: "painting", 283: "painting", 284: "painting", 285: "painting",
    286: "painting", 287: "painting", 288: "painting", 289: "painting", 290: "painting",
    291: "veterinary", 292: "veterinary", 293: "veterinary", 294: "veterinary",
    295: "veterinary", 296: "veterinary", 297: "veterinary", 298: "veterinary",
    299: "veterinary", 300: "veterinary",
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
    images = get_images(num)

    pareto_imgs = [i for i in images if "pareto_" in i]
    main_effect_imgs = [i for i in images if "main_effects_" in i]
    rsm_imgs = [i for i in images if "rsm_" in i]

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
        "settings": {"operation": design, "test_script": f"use_cases/{num:02d}_{slug}/sim.sh"}
    }, indent=2)

    config_html = escape(config_display)
    config_html = re.sub(r'"([^"]+)":', r'<span class="key">"\1"</span>:', config_html)
    config_html = re.sub(r': "([^"]*)"', r': <span class="string">"\1"</span>', config_html)

    matrix_html = build_matrix_html(config_path, design_label)

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

        pareto = [i for i in pareto_imgs if rname in i]
        me = [i for i in main_effect_imgs if rname in i]

        if pareto or me:
            analysis_html += '    <div class="results-grid">\n'
            for img in pareto:
                analysis_html += f'      <div>\n        <p class="caption">Pareto Chart</p>\n        <img src="../images/{img}" alt="Pareto chart for {escape(rname)}">\n      </div>\n'
            for img in me:
                analysis_html += f'      <div>\n        <p class="caption">Main Effects Plot</p>\n        <img src="../images/{img}" alt="Main effects plot for {escape(rname)}">\n      </div>\n'
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
        prev_dirs = glob.glob(f"use_cases/{prev_num:02d}_*")
        if prev_dirs:
            prev_slug = os.path.basename(prev_dirs[0]).split("_", 1)[1]
            prev_web = slug_to_web(prev_slug)
            prev_cfg = json.load(open(os.path.join(prev_dirs[0], "config.json")))
            prev_name = prev_cfg["metadata"]["name"]
            prev_link = f'<a href="{prev_num:02d}-{prev_web}.html">&larr; Previous: {escape(prev_name)}</a>'

    if next_num <= 300:
        next_dirs = glob.glob(f"use_cases/{next_num:02d}_*")
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

<div class="container-narrow uc-content">

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
          <div class="code-body"><span class="prompt">$ </span>python doe.py info <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">2</div>
      <div class="uc-step-body">
        <h3>Generate the runner script</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>python doe.py generate <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json \\
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
          <div class="code-body"><span class="prompt">$ </span>python doe.py analyze <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">5</div>
      <div class="uc-step-body">
        <h3>Get optimization recommendations</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>python doe.py optimize <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json</div>
        </div>
      </div>
    </div>

    <div class="uc-step">
      <div class="uc-step-num">6</div>
      <div class="uc-step-body">
        <h3>Generate the HTML report</h3>
        <div class="code-block">
          <div class="code-header"><span>Terminal</span><button class="code-copy">Copy</button></div>
          <div class="code-body"><span class="prompt">$ </span>python doe.py report <span class="flag">--config</span> use_cases/{num:02d}_{slug}/config.json \\
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
    if not matrix_html:
        return

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

    # Remove any previously injected matrix section
    page = re.sub(
        r'\n  <!-- Experimental Matrix -->.*?</section>\n',
        '',
        page,
        flags=re.DOTALL,
    )

    # Insert before the Workflow section — try comment marker first, then h2 text
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

    with open(html_path, "w") as f:
        f.write(page)
    print(f"  [{num:02d}] injected matrix into {os.path.basename(html_path)}")


def main():
    # Generate pages for use cases 27-300
    for num in range(27, 301):
        pattern = f"use_cases/{num:02d}_*" if num < 100 else f"use_cases/{num}_*"
        dirs = glob.glob(pattern)
        if dirs:
            build_page(num, dirs[0])
    print(f"\n  274 HTML pages generated (27-300).")

    # Inject experimental matrix into existing pages for use cases 1-26
    print("\nInjecting experimental matrices into use cases 1-26...")
    for num in range(1, 27):
        dirs = glob.glob(f"use_cases/{num:02d}_*")
        if dirs:
            inject_matrix_into_existing(num, dirs[0])
    print(f"\nDone: all use case pages updated with experimental matrices.")


if __name__ == "__main__":
    main()
