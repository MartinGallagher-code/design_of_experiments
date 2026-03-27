#!/usr/bin/env python3
# Copyright (C) 2026 Martin J. Gallagher
# Licensed under the GNU General Public License v3.0 or later.
"""Generate PowerPoint slides for the DOE Helper Training Course.

Design language matches doehelper.com:
  - Indigo gradient hero backgrounds (#1e1b4b -> #6366f1)
  - Purple accent (#5046e5)
  - Light content slides with subtle purple tints
  - Dark code blocks (#1a1a1a)
  - Amber/orange for exercises, green for key-points
  - Inter + Consolas typography

Run:  python generate_slides.py
Output: slides/ directory with 8 .pptx files.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ── Website colour palette ─────────────────────────────────
INDIGO_DEEP   = RGBColor(0x1E, 0x1B, 0x4B)   # hero gradient start
INDIGO_MID    = RGBColor(0x31, 0x2E, 0x81)   # hero gradient mid
INDIGO_BRIGHT = RGBColor(0x43, 0x38, 0xCA)   # hero gradient end
VIOLET        = RGBColor(0x63, 0x66, 0xF1)   # lighter accent
ACCENT        = RGBColor(0x50, 0x46, 0xE5)   # primary purple accent
ACCENT_LIGHT  = RGBColor(0xEE, 0xF2, 0xFF)   # pale purple bg
ACCENT_WASH   = RGBColor(0xF5, 0xF3, 0xFF)   # very pale purple

WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
OFF_WHITE     = RGBColor(0xFA, 0xFA, 0xFA)   # --bg from site
INK           = RGBColor(0x11, 0x11, 0x11)   # --ink
FG            = RGBColor(0x33, 0x33, 0x33)   # --fg body text
MUTED         = RGBColor(0x66, 0x66, 0x66)   # --muted
FAINT         = RGBColor(0x99, 0x99, 0x99)   # --faint
BORDER        = RGBColor(0xE5, 0xE5, 0xE5)   # --border

TEAL          = RGBColor(0x0D, 0x94, 0x88)
TEAL_LIGHT    = RGBColor(0xF0, 0xFD, 0xFA)
GREEN         = RGBColor(0x16, 0xA3, 0x4A)
GREEN_LIGHT   = RGBColor(0xF0, 0xFD, 0xF4)
AMBER         = RGBColor(0xD9, 0x77, 0x06)
AMBER_LIGHT   = RGBColor(0xFF, 0xFB, 0xEB)
ROSE          = RGBColor(0xE1, 0x1D, 0x48)

CODE_BG       = RGBColor(0x1A, 0x1A, 0x1A)   # website code block bg
CODE_HEADER   = RGBColor(0x22, 0x22, 0x22)   # code header bg
CODE_TEXT     = RGBColor(0xCC, 0xCC, 0xCC)   # code body text
CODE_GREEN    = RGBColor(0x6E, 0xC8, 0x6E)   # prompt colour
CODE_BLUE     = RGBColor(0x8B, 0x9C, 0xF7)   # flag colour
CODE_AMBER    = RGBColor(0xE5, 0xA6, 0x4E)   # string colour

FONT_BODY = "Inter"
FONT_MONO = "Consolas"

os.makedirs("slides", exist_ok=True)


# ═══════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════

def new_prs():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _fill_bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def _rect(slide, x, y, w, h, fill, line=False):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if not line:
        s.line.fill.background()
    return s


def _rounded(slide, x, y, w, h, fill, line=False):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if not line:
        s.line.fill.background()
    return s


def _text(slide, x, y, w, h, text, size=20, color=FG, bold=False,
          font=FONT_BODY, align=PP_ALIGN.LEFT, anchor=None):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    if anchor:
        tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    return tf


def _copyright(slide):
    _text(slide, Inches(0.8), Inches(7.0), Inches(11), Inches(0.4),
          "\u00a9 2026 Martin J. Gallagher  |  GPL-3.0-or-later  |  doehelper.com",
          size=10, color=FAINT, font=FONT_MONO)


def _bullets(slide, x, y, w, h, items, size=19, color=FG, spacing=7):
    """Render bullet list. Prefix '>> ' for sub-bullets."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, raw in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        indent = 0
        text = raw
        while text.startswith(">> "):
            indent += 1
            text = text[3:]
        p.text = text
        p.font.size = Pt(size - 2 * indent)
        p.font.color.rgb = color if indent == 0 else MUTED
        p.font.name = FONT_BODY
        p.space_after = Pt(spacing)
        p.level = indent
    return tf


def _slide_number(slide, num, total=None):
    label = f"{num}" if total is None else f"{num}/{total}"
    _text(slide, Inches(12.2), Inches(7.0), Inches(1), Inches(0.4),
          label, size=10, color=FAINT, font=FONT_MONO, align=PP_ALIGN.RIGHT)


# ═══════════════════════════════════════════════════════════
# Slide templates (matching website design)
# ═══════════════════════════════════════════════════════════

def add_title_slide(prs, title, subtitle, module_num=None):
    """Dark indigo gradient hero — matches website hero section."""
    slide = _blank(prs)
    _fill_bg(slide, INDIGO_DEEP)

    # Layered indigo panels to simulate gradient
    _rect(slide, Inches(0), Inches(0), Inches(6.5), SLIDE_H, INDIGO_DEEP)
    _rect(slide, Inches(6.5), Inches(0), Inches(3.5), SLIDE_H, INDIGO_MID)
    _rect(slide, Inches(10), Inches(0), Inches(3.333), SLIDE_H, INDIGO_BRIGHT)

    # Subtle decorative accent bar (left edge, like website sidebar)
    _rect(slide, Inches(0), Inches(0), Inches(0.08), SLIDE_H, VIOLET)

    # Decorative circle blobs (mimic website decoration washes)
    c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9), Inches(-1), Inches(5), Inches(5))
    c1.fill.solid()
    c1.fill.fore_color.rgb = VIOLET
    c1.fill.fore_color.brightness = 0.3
    c1.line.fill.background()

    c2 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(-1), Inches(4), Inches(4), Inches(4))
    c2.fill.solid()
    c2.fill.fore_color.rgb = ACCENT
    c2.fill.fore_color.brightness = 0.4
    c2.line.fill.background()

    # Module badge (monospace uppercase — matches website section labels)
    if module_num is not None:
        badge = _rounded(slide, Inches(1.0), Inches(1.5), Inches(2.6), Inches(0.48),
                         INDIGO_MID)
        btf = badge.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        btf.margin_left = Inches(0.15)
        p = btf.paragraphs[0]
        p.text = f"MODULE {module_num}"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(0xC7, 0xD2, 0xFE)  # light indigo
        p.font.bold = True
        p.font.name = FONT_MONO
        p.alignment = PP_ALIGN.LEFT

    # Title
    _text(slide, Inches(1.0), Inches(2.5), Inches(10), Inches(2.2),
          title, size=40, color=WHITE, bold=True)

    # Subtitle
    _text(slide, Inches(1.0), Inches(4.8), Inches(9.5), Inches(1.5),
          subtitle, size=19, color=RGBColor(0xA5, 0xB4, 0xFC))

    # Copyright
    _text(slide, Inches(0.8), Inches(7.0), Inches(11), Inches(0.4),
          "\u00a9 2026 Martin J. Gallagher  |  GPL-3.0-or-later  |  doehelper.com",
          size=10, color=RGBColor(0x63, 0x66, 0xF1), font=FONT_MONO)


def add_content_slide(prs, title, bullets_list, accent_bar=True):
    """Light slide with purple accent top bar — matches website content pages."""
    slide = _blank(prs)
    _fill_bg(slide, OFF_WHITE)

    if accent_bar:
        _rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.05), ACCENT)

    # Left accent stripe (like website callout borders)
    _rect(slide, Inches(0.6), Inches(0.45), Inches(0.04), Inches(0.55), ACCENT)

    _text(slide, Inches(0.85), Inches(0.4), Inches(11), Inches(0.7),
          title, size=28, color=INK, bold=True)

    _bullets(slide, Inches(0.9), Inches(1.3), Inches(11.2), Inches(5.6),
             bullets_list, size=19, color=FG, spacing=6)
    _copyright(slide)
    return slide


def add_code_slide(prs, title, code_text, note=""):
    """Dark code block on light background — matches website code blocks."""
    slide = _blank(prs)
    _fill_bg(slide, OFF_WHITE)

    # Green accent bar (like website success/teal callout)
    _rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.05), TEAL)

    _text(slide, Inches(0.85), Inches(0.35), Inches(11), Inches(0.6),
          title, size=26, color=INK, bold=True)

    # Code container — matches website .code-block
    code_y = Inches(1.15)
    code_h = Inches(4.8) if not note else Inches(4.3)

    # Header bar
    _rect(slide, Inches(0.6), code_y, Inches(12), Inches(0.35), CODE_HEADER)
    _text(slide, Inches(0.9), code_y, Inches(4), Inches(0.35),
          "terminal", size=10, color=FAINT, font=FONT_MONO,
          anchor=MSO_ANCHOR.MIDDLE)

    # Code body
    body = _rounded(slide, Inches(0.6), code_y + Inches(0.35),
                    Inches(12), code_h, CODE_BG)
    tf = body.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.2)
    tf.margin_right = Inches(0.3)
    lines = code_text.strip().split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        # Colour prompt lines green, comments gray, rest default
        if line.strip().startswith("$"):
            p.font.color.rgb = CODE_GREEN
        elif line.strip().startswith("#"):
            p.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        else:
            p.font.color.rgb = CODE_TEXT
        p.font.size = Pt(15)
        p.font.name = FONT_MONO
        p.space_after = Pt(1)

    if note:
        _text(slide, Inches(0.9), Inches(5.85), Inches(11), Inches(0.7),
              note, size=14, color=MUTED, font=FONT_BODY)

    _copyright(slide)
    return slide


def add_two_col_slide(prs, title, left_items, right_items,
                      left_title="", right_title=""):
    """Two-column layout with card-style boxes — matches website comparison cards."""
    slide = _blank(prs)
    _fill_bg(slide, OFF_WHITE)
    _rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.05), ACCENT)

    _rect(slide, Inches(0.6), Inches(0.45), Inches(0.04), Inches(0.55), ACCENT)
    _text(slide, Inches(0.85), Inches(0.4), Inches(11), Inches(0.7),
          title, size=28, color=INK, bold=True)

    col_y = Inches(1.3)
    card_h = Inches(5.4)

    # Left card (green tint — like website .comparison-card.good)
    _rounded(slide, Inches(0.6), col_y, Inches(5.8), card_h, GREEN_LIGHT)
    _rect(slide, Inches(0.6), col_y, Inches(0.04), card_h, GREEN)

    if left_title:
        _text(slide, Inches(0.9), col_y + Inches(0.15), Inches(5.2), Inches(0.4),
              left_title, size=16, color=GREEN, bold=True, font=FONT_MONO)
    lt_y = col_y + (Inches(0.6) if left_title else Inches(0.15))
    _bullets(slide, Inches(0.9), lt_y, Inches(5.2), Inches(4.5),
             left_items, size=17, color=FG, spacing=5)

    # Right card (purple tint — like website .keypoint-box)
    _rounded(slide, Inches(6.8), col_y, Inches(5.8), card_h, ACCENT_LIGHT)
    _rect(slide, Inches(6.8), col_y, Inches(0.04), card_h, ACCENT)

    if right_title:
        _text(slide, Inches(7.1), col_y + Inches(0.15), Inches(5.2), Inches(0.4),
              right_title, size=16, color=ACCENT, bold=True, font=FONT_MONO)
    rt_y = col_y + (Inches(0.6) if right_title else Inches(0.15))
    _bullets(slide, Inches(7.1), rt_y, Inches(5.2), Inches(4.5),
             right_items, size=17, color=FG, spacing=5)

    _copyright(slide)
    return slide


def add_exercise_slide(prs, title, instructions):
    """Amber-tinted card — matches website .callout.warning style."""
    slide = _blank(prs)
    _fill_bg(slide, OFF_WHITE)

    # Amber accent bar
    _rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.05), AMBER)

    # Badge (like website step-badge)
    badge = _rounded(slide, Inches(0.6), Inches(0.3), Inches(2.4), Inches(0.5), AMBER)
    btf = badge.text_frame
    btf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = btf.paragraphs[0]
    p.text = "HANDS-ON EXERCISE"
    p.font.size = Pt(13)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = FONT_MONO
    p.alignment = PP_ALIGN.CENTER

    _text(slide, Inches(3.3), Inches(0.3), Inches(9), Inches(0.6),
          title, size=26, color=INK, bold=True)

    # Instruction card with amber left border (callout style)
    card = _rounded(slide, Inches(0.6), Inches(1.1), Inches(12), Inches(5.6),
                    AMBER_LIGHT)
    _rect(slide, Inches(0.6), Inches(1.1), Inches(0.04), Inches(5.6), AMBER)

    _bullets(slide, Inches(0.9), Inches(1.25), Inches(11.4), Inches(5.3),
             instructions, size=17, color=FG, spacing=5)

    _copyright(slide)
    return slide


def add_key_point_slide(prs, title, points):
    """Dark indigo background with card rows — matches website keypoint boxes on dark."""
    slide = _blank(prs)
    _fill_bg(slide, INDIGO_DEEP)

    # Simulated gradient panels
    _rect(slide, Inches(4), Inches(0), Inches(5), SLIDE_H, INDIGO_MID)
    _rect(slide, Inches(9), Inches(0), Inches(4.333), SLIDE_H, INDIGO_BRIGHT)

    _text(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.7),
          title, size=30, color=WHITE, bold=True)

    y = Inches(1.4)
    row_h = Inches(0.85)
    gap = Inches(0.12)
    for point in points:
        card = _rounded(slide, Inches(0.8), y, Inches(11.5), row_h,
                        INDIGO_MID)
        # Left accent dot (like website step badge)
        dot = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(1.1), y + Inches(0.25), Inches(0.35), Inches(0.35))
        dot.fill.solid()
        dot.fill.fore_color.rgb = ACCENT
        dot.line.fill.background()

        _text(slide, Inches(1.7), y + Inches(0.05), Inches(10.3), row_h,
              point, size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        y += row_h + gap

    _text(slide, Inches(0.8), Inches(7.0), Inches(11), Inches(0.4),
          "\u00a9 2026 Martin J. Gallagher  |  GPL-3.0-or-later",
          size=10, color=VIOLET, font=FONT_MONO)


def add_section_divider(prs, section_title, section_desc=""):
    """Full-bleed indigo slide for section breaks — matches website hero."""
    slide = _blank(prs)
    _fill_bg(slide, INDIGO_MID)

    # Decorative ovals
    c1 = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8), Inches(-2), Inches(6), Inches(6))
    c1.fill.solid()
    c1.fill.fore_color.rgb = INDIGO_BRIGHT
    c1.fill.fore_color.brightness = 0.2
    c1.line.fill.background()

    _text(slide, Inches(1), Inches(2.5), Inches(11), Inches(2),
          section_title, size=42, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

    if section_desc:
        _text(slide, Inches(2), Inches(4.6), Inches(9), Inches(1),
              section_desc, size=20, color=RGBColor(0xC7, 0xD2, 0xFE),
              align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════
# MODULE 1
# ═══════════════════════════════════════════════════════════

def build_module_1():
    prs = new_prs()

    add_title_slide(prs,
        "Introduction to\nDesign of Experiments",
        "Why systematic experimentation beats trial-and-error\nDOE Helper Training Course",
        module_num=1)

    add_content_slide(prs, "What You Will Learn", [
        "What Design of Experiments (DOE) is and why it matters",
        "The cost of unplanned experiments",
        "The One-Variable-At-a-Time (OVAT) trap",
        "Core DOE concepts: factors, levels, responses, effects",
        "How doe-helper automates the DOE workflow",
        "When to use DOE vs. other approaches",
    ])

    add_content_slide(prs, "What is Design of Experiments?", [
        "A systematic method for planning experiments",
        ">> Change multiple factors simultaneously",
        ">> Use statistical principles to extract maximum information",
        ">> Minimise the number of experimental runs needed",
        "Pioneered by R.A. Fisher in the 1920s for agriculture",
        "Extended by Taguchi, Box, and others for industry",
        "Now applied to software, cloud, manufacturing, and beyond",
    ])

    add_two_col_slide(prs, "The Cost of Unplanned Experiments",
        [
            "Ad-hoc testing wastes resources",
            "Interactions between factors are missed",
            "Conclusions drawn from insufficient data",
            "Optimisation gets stuck in local optima",
            "Results are not reproducible",
        ],
        [
            "A web team ran 47 ad-hoc tests over 3 months",
            "Found: only 2 factors mattered",
            "A 2-factor full factorial needed just 4 runs",
            "DOE saved 43 runs and 11 weeks",
        ],
        left_title="THE PROBLEM",
        right_title="REAL-WORLD EXAMPLE"
    )

    add_content_slide(prs, "The OVAT Trap", [
        "One-Variable-At-a-Time: change one factor, hold others constant",
        "Seems logical but has critical flaws:",
        ">> Misses interactions between factors entirely",
        ">> Requires more runs to learn the same amount",
        ">> Can converge on the wrong optimum",
        "Example: tuning a web server",
        ">> OVAT: 3 factors \u00d7 3 levels = 9 runs, misses interactions",
        ">> Full factorial: 2\u00b3 = 8 runs, captures all interactions",
    ])

    add_content_slide(prs, "Core DOE Concepts", [
        "Factor \u2014 a variable you control (e.g. temperature, cache size)",
        "Level \u2014 specific value of a factor (e.g. low/high, 100/200/300)",
        "Response \u2014 what you measure (e.g. throughput, yield, cost)",
        "Main Effect \u2014 the average impact of one factor on the response",
        "Interaction \u2014 when the effect of one factor depends on another",
        "Design Matrix \u2014 the table of all planned experimental runs",
        "Randomisation \u2014 running in random order to avoid bias",
    ])

    add_content_slide(prs, "Effect Sparsity Principle", [
        "In most systems only a few factors have large effects",
        "Most interactions are negligible",
        "This is the \"Pareto of experimentation\"",
        "Screening designs exploit this: test many factors cheaply",
        "Then focus detailed experiments on the vital few",
        "doe-helper supports this: screen \u2192 refine \u2192 optimise",
    ])

    add_content_slide(prs, "The DOE Workflow", [
        "1.  Define objectives \u2014 what do you want to learn or optimise?",
        "2.  Select factors and levels \u2014 what can you control?",
        "3.  Choose a design \u2014 how many runs can you afford?",
        "4.  Generate the design matrix and run experiments",
        "5.  Analyse results \u2014 which factors matter?",
        "6.  Interpret and act \u2014 confirm, refine, or optimise",
        "doe-helper automates steps 3\u20136 and guides 1\u20132",
    ])

    add_code_slide(prs, "Meet doe-helper", """
$ pip install doehelper

$ doe init reactor --design full_factorial
  Created: reactor/config.json

$ doe generate reactor/
  Design matrix written to reactor/design.csv
  Runner script written to reactor/run.sh

$ doe analyze reactor/
  ANOVA table, Pareto chart, main-effects plots

$ doe optimize reactor/
  Recommended: temperature=180, pressure=3.5
""", "doe-helper provides a complete CLI workflow from design to optimisation")

    add_key_point_slide(prs, "Key Takeaways", [
        "DOE is a systematic, statistically rigorous way to experiment",
        "OVAT wastes runs and misses interactions",
        "Effect sparsity: most systems have only a few important factors",
        "doe-helper automates the entire DOE workflow via the CLI",
        "The workflow: define \u2192 design \u2192 run \u2192 analyse \u2192 optimise",
    ])

    add_exercise_slide(prs, "Exercise 1: Explore doe-helper", [
        "1. Install doe-helper:  pip install doehelper",
        "2. Run:  doe --help   and read the available commands",
        "3. Run:  doe init coffee_brewing --design full_factorial",
        "4. Open  coffee_brewing/config.json  and examine the template",
        "5. Identify the factors, levels, and responses",
        "",
        "Bonus: Think of a problem in your own work where OVAT",
        "has been used. How many factors and levels would a",
        "proper DOE need?",
    ])

    prs.save("slides/Module_01_Introduction_to_DOE.pptx")
    print("  Module 1 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 2
# ═══════════════════════════════════════════════════════════

def build_module_2():
    prs = new_prs()

    add_title_slide(prs,
        "Getting Started\nwith doe-helper",
        "Installation, configuration, and your first experiment",
        module_num=2)

    add_content_slide(prs, "Learning Objectives", [
        "Install doe-helper and verify the setup",
        "Understand the config.json structure",
        "Define factors (continuous, categorical, ordinal)",
        "Define responses and their targets",
        "Configure design settings (randomisation, blocks, replicates)",
        "Use doe init with built-in templates",
    ])

    add_code_slide(prs, "Installation", """
# Install from PyPI
$ pip install doehelper

# Verify installation
$ doe --help

# Check version
$ doe --version
doehelper 0.1.0

# Requirements: Python 3.10+
# Works on Linux, macOS, Windows
# Deps: numpy, pandas, scipy, matplotlib, pyDOE3, Jinja2
""")

    add_code_slide(prs, "Creating Your First Experiment", """
# Use a built-in template
$ doe init my_experiment --design full_factorial

# Or create config.json manually
$ mkdir my_experiment && cat > my_experiment/config.json << 'EOF'
{
  "factors": {
    "temperature": {"low": 150, "high": 200, "units": "C"},
    "pressure":    {"low": 1.0, "high": 5.0, "units": "bar"},
    "catalyst":    {"low": 0.5, "high": 1.5, "units": "g"}
  },
  "responses": {
    "yield": {"units": "%", "target": "maximize"}
  },
  "design": {"type": "full_factorial"}
}
EOF
""")

    add_two_col_slide(prs, "Factor Types",
        [
            "Continuous: numeric range with low/high",
            ">> temperature: 150\u2013200",
            ">> pressure: 1.0\u20135.0",
            "",
            "Coded variables: factors are internally",
            "scaled to \u22121 / +1 so all effects are",
            "directly comparable",
        ],
        [
            "Categorical: discrete named levels",
            ">> material: steel, aluminum, titanium",
            "",
            "Ordinal: ordered categories",
            ">> quality: low, medium, high",
            "",
            "Set \"type\" field in config.json",
        ],
        left_title="CONTINUOUS",
        right_title="CATEGORICAL & ORDINAL"
    )

    add_code_slide(prs, "Factor Configuration Examples", """
"factors": {
    "temperature": {
        "low": 150, "high": 200, "units": "C"
    },
    "material": {
        "type": "categorical",
        "levels": ["steel", "aluminum", "titanium"]
    },
    "quality_grade": {
        "type": "ordinal",
        "levels": ["low", "medium", "high"]
    }
}
""", "Continuous factors use low/high; categorical and ordinal use a levels list")

    add_content_slide(prs, "Response Configuration", [
        "Each response has a name, units, and a target direction",
        "Target options:",
        ">> \"maximize\" \u2014 higher is better (yield, throughput)",
        ">> \"minimize\" \u2014 lower is better (cost, latency, defects)",
        ">> A specific number \u2014 hit a target (pH = 7.0)",
        "Multiple responses are supported for multi-objective optimisation",
        ">> doe-helper uses desirability functions to balance trade-offs",
    ])

    add_content_slide(prs, "Design Settings", [
        "The \"design\" section controls experiment structure:",
        ">> type: design type (full_factorial, ccd, box_behnken, etc.)",
        ">> randomize: true/false \u2014 randomise run order (default: true)",
        ">> replicates: number of times to repeat each run",
        ">> center_points: add center points for curvature detection",
        ">> blocks: number of blocks for nuisance variables",
        ">> resolution: for fractional factorials (III, IV, V)",
    ])

    add_code_slide(prs, "Complete config.json Example", """
{
  "factors": {
    "temperature": {"low": 150, "high": 200, "units": "C"},
    "pressure":    {"low": 1.0, "high": 5.0, "units": "bar"},
    "catalyst":    {"low": 0.5, "high": 1.5, "units": "g"}
  },
  "responses": {
    "yield":  {"units": "%", "target": "maximize"},
    "purity": {"units": "%", "target": "maximize"}
  },
  "design": {
    "type": "full_factorial",
    "randomize": true,
    "center_points": 3
  }
}
""", "This config produces 2\u00b3 = 8 runs + 3 center points = 11 total runs")

    add_content_slide(prs, "Built-in Templates (doe init)", [
        "doe-helper includes 221 worked use-case templates",
        "Categories include:",
        ">> Cloud/DevOps: Kubernetes, CI/CD, database tuning",
        ">> Manufacturing: 3D printing, injection molding, chemical processes",
        ">> Food science: coffee brewing, bread baking, fermentation",
        ">> IoT/Electronics: sensor calibration, motor control",
        ">> Sports/Health: training programs, sleep optimisation",
        "Templates provide config.json + simulation scripts for practice",
    ])

    add_code_slide(prs, "Verifying with doe info", """
$ doe info my_experiment/

Design Summary
  Type:           full_factorial
  Factors:        3
  Runs:           11 (8 factorial + 3 center)
  Replicates:     1
  Randomized:     yes

Design Evaluation
  D-efficiency:   100.0%
  A-efficiency:   100.0%
  G-efficiency:   100.0%
""", "Always run doe info to verify your design before running experiments")

    add_exercise_slide(prs, "Exercise 2: Build a Configuration", [
        "Scenario: optimising a web application's performance.",
        "",
        "1. Create a directory:  mkdir webapp_perf",
        "2. Create config.json with these factors:",
        ">> cache_size: 64\u2013512 MB",
        ">> thread_count: 4\u201332",
        ">> compression: categorical [none, gzip, brotli]",
        "3. Add responses: response_time_ms (min), throughput_rps (max)",
        "4. Set design type to full_factorial",
        "5. Run:  doe info webapp_perf/   to verify",
        "6. Run:  doe generate webapp_perf/   to see the design matrix",
    ])

    prs.save("slides/Module_02_Getting_Started.pptx")
    print("  Module 2 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 3
# ═══════════════════════════════════════════════════════════

def build_module_3():
    prs = new_prs()

    add_title_slide(prs,
        "Full Factorial Designs",
        "Understanding and running complete two-level experiments",
        module_num=3)

    add_content_slide(prs, "Learning Objectives", [
        "Understand full factorial (2\u1d4f) designs",
        "Calculate the number of runs needed",
        "Interpret main effects and interactions",
        "Generate and run a full factorial with doe-helper",
        "Read ANOVA tables and Pareto charts",
        "Know when full factorial is the right choice",
    ])

    add_content_slide(prs, "What is a Full Factorial Design?", [
        "Tests every combination of factor levels",
        "For k factors at 2 levels: 2\u1d4f runs",
        ">> 2 factors: 4 runs   |   3 factors: 8 runs",
        ">> 4 factors: 16 runs  |   5 factors: 32 runs",
        "Estimates ALL main effects and ALL interactions",
        "The \"gold standard\" of experimental designs",
        "Practical limit: \u22645\u20136 factors (32\u201364 runs)",
    ])

    add_two_col_slide(prs, "2\u00b2 Full Factorial Example",
        [
            "Factor A: Temperature (150, 200)",
            "Factor B: Pressure (1, 5)",
            "",
            "Run 1: A=low,  B=low   \u2192 62%",
            "Run 2: A=high, B=low   \u2192 74%",
            "Run 3: A=low,  B=high  \u2192 68%",
            "Run 4: A=high, B=high  \u2192 91%",
        ],
        [
            "Main effect A:",
            "  [(74+91)\u2212(62+68)] / 2 = 17.5%",
            "",
            "Main effect B:",
            "  [(68+91)\u2212(62+74)] / 2 = 11.5%",
            "",
            "Interaction AB:",
            "  [(62+91)\u2212(74+68)] / 2 = 5.5%",
        ],
        left_title="DESIGN MATRIX & RESULTS",
        right_title="EFFECT CALCULATIONS"
    )

    add_content_slide(prs, "Why Interactions Matter", [
        "An interaction means the effect of one factor depends on another",
        "OVAT cannot detect interactions at all",
        "Example: Temperature alone increases yield by 17.5%",
        ">> But at high pressure, the temperature boost is even larger",
        ">> The combination is more powerful than either alone",
        "Interactions can be antagonistic too (cancel each other out)",
        "Full factorials capture all of these relationships",
    ])

    add_code_slide(prs, "Running a Full Factorial with doe-helper", """
# 1. Configure
$ cat > seal_strength/config.json << 'EOF'
{
  "factors": {
    "temperature": {"low": 225, "high": 285, "units": "F"},
    "pressure":    {"low": 40,  "high": 90,  "units": "psi"},
    "dwell_time":  {"low": 1.0, "high": 3.5, "units": "sec"}
  },
  "responses": {
    "seal_strength": {"units": "g/in", "target": "maximize"}
  },
  "design": {"type": "full_factorial", "center_points": 3}
}
EOF

# 2. Generate, run, analyse
$ doe generate seal_strength/
$ doe record seal_strength/
$ doe analyze seal_strength/
""")

    add_content_slide(prs, "Reading the ANOVA Table", [
        "ANOVA = Analysis of Variance",
        "Source \u2014 factor or interaction name",
        "SS \u2014 Sum of Squares (variability explained)",
        "DF \u2014 Degrees of Freedom",
        "MS \u2014 Mean Square (SS / DF)",
        "F-value \u2014 test statistic (higher = stronger effect)",
        "p-value \u2014 probability effect is due to chance",
        "Rule of thumb: p < 0.05 means the factor is significant",
    ])

    add_content_slide(prs, "Pareto Chart & Center Points", [
        "Pareto chart: bar chart of absolute effect magnitudes",
        ">> Sorted largest to smallest",
        ">> Dashed line shows significance threshold",
        ">> Bars above the line are statistically significant",
        ">> Quickly identifies the \"vital few\" factors",
        "",
        "Center points: extra runs at the midpoint of all factors",
        ">> Detect curvature (non-linear effects)",
        ">> Cheap insurance: 3\u20135 center points cost little",
    ])

    add_key_point_slide(prs, "Key Takeaways", [
        "Full factorial = every combination, captures all effects",
        "2\u1d4f runs: practical for up to ~5\u20136 factors",
        "Interactions are why DOE beats OVAT",
        "Center points detect curvature cheaply",
        "doe-helper automates generation, recording, and analysis",
    ])

    add_exercise_slide(prs, "Exercise 3: Seal Strength Experiment", [
        "1. Create the seal_strength experiment from the slide",
        "2. Run:  doe generate seal_strength/",
        "3. Run:  doe info seal_strength/  \u2014 how many runs?",
        "4. Run the simulation:  bash seal_strength/run.sh",
        "5. Run:  doe analyze seal_strength/",
        "6. Answer these questions:",
        ">> Which factor has the largest main effect?",
        ">> Are there significant interactions?",
        ">> Is there evidence of curvature from center points?",
        "7. Run:  doe report seal_strength/  and open the HTML report",
    ])

    prs.save("slides/Module_03_Full_Factorial.pptx")
    print("  Module 3 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 4
# ═══════════════════════════════════════════════════════════

def build_module_4():
    prs = new_prs()

    add_title_slide(prs,
        "Fractional Factorial &\nScreening Designs",
        "Testing many factors efficiently when resources are limited",
        module_num=4)

    add_content_slide(prs, "Learning Objectives", [
        "Understand why fractional factorials exist",
        "Learn about resolution and aliasing",
        "Use Plackett-Burman and Definitive Screening designs",
        "Choose the right screening design with doe-helper",
        "Interpret confounded effects",
        "Plan a follow-up experiment after screening",
    ])

    add_content_slide(prs, "The Problem: Too Many Factors", [
        "Full factorial with 7 factors = 128 runs",
        "With 10 factors = 1,024 runs",
        "With 15 factors = 32,768 runs!",
        "In practice, experiments often start with 6\u201320 factors",
        "Effect sparsity says most factors won't matter",
        "Solution: run a fraction of the full factorial",
    ])

    add_content_slide(prs, "Fractional Factorial Designs", [
        "Run 2\u1d4f\u207b\u1d56 instead of 2\u1d4f runs",
        ">> 2\u2077\u207b\u2074 = 8 runs instead of 128 for 7 factors",
        ">> 2\u2076\u207b\u00b2 = 16 runs instead of 64 for 6 factors",
        "Trade-off: some effects become aliased (confounded)",
        "Resolution tells you what is confounded:",
        ">> Res III: main effects aliased with 2-factor interactions",
        ">> Res IV: main effects clear, 2FI aliased with each other",
        ">> Res V: main effects and 2FI all clear",
    ])

    add_code_slide(prs, "Fractional Factorial with doe-helper", """
{
  "factors": {
    "A": {"low": -1, "high": 1},
    "B": {"low": -1, "high": 1},
    "C": {"low": -1, "high": 1},
    "D": {"low": -1, "high": 1},
    "E": {"low": -1, "high": 1},
    "F": {"low": -1, "high": 1},
    "G": {"low": -1, "high": 1}
  },
  "responses": {
    "performance": {"units": "score", "target": "maximize"}
  },
  "design": {"type": "fractional_factorial"}
}

$ doe generate screening/
$ doe info screening/       # shows aliasing structure
""")

    add_two_col_slide(prs, "Plackett-Burman vs. Definitive Screening",
        [
            "Plackett-Burman (PB)",
            "Run counts: multiples of 4 (12, 20, 24\u2026)",
            "Screen up to N\u22121 factors in N runs",
            "Resolution III",
            "Main effects aliased with 2FIs",
            "No curvature detection",
            "Best for: initial rough screening",
        ],
        [
            "Definitive Screening (DSD)",
            "2k+1 runs for k factors",
            "Three-level design (low/mid/high)",
            "Main effects NOT aliased with 2FIs",
            "Can detect curvature",
            "Modern best practice (Jones 2011)",
            "Best for: cleaner screening",
        ],
        left_title="PLACKETT-BURMAN",
        right_title="DEFINITIVE SCREENING"
    )

    add_content_slide(prs, "The Screening Workflow", [
        "Phase 1: Screen",
        ">> Run PB or DSD with all candidate factors",
        ">> Identify 3\u20135 significant factors, drop the rest",
        "Phase 2: Characterise",
        ">> Full factorial on surviving factors",
        ">> Estimate all interactions, check for curvature",
        "Phase 3: Optimise",
        ">> Response surface design (CCD, Box-Behnken)",
        ">> doe optimize for final settings",
    ])

    add_code_slide(prs, "Fold-Over with doe augment", """
# After screening, de-alias confounded effects:
$ doe augment api_screening/ --method fold-over

# Mirrors the original design to break aliases
# Doubles run count but separates confounded effects

# Other augmentation methods:
$ doe augment experiment/ --method center-points --count 5
$ doe augment experiment/ --method star-points
""", "doe augment extends an existing design without starting over")

    add_key_point_slide(prs, "Key Takeaways", [
        "Fractional factorials trade runs for information (aliasing)",
        "Resolution tells you what's confounded with what",
        "Plackett-Burman: maximum screening efficiency",
        "Definitive Screening: modern, cleaner main-effect estimates",
        "doe augment extends designs with fold-overs and star points",
    ])

    add_exercise_slide(prs, "Exercise 4: Screening a Microservice", [
        "Scenario: 8 factors that might affect API latency.",
        "",
        "1. Create config.json with 8 continuous factors",
        "2. Set design type to \"plackett_burman\"",
        "3. Run:  doe generate microservice/",
        ">> How many runs does the design require?",
        "4. Compare: change to \"definitive_screening\"",
        ">> How many runs now? What's different?",
        "5. Run the simulation and analyse results",
        "6. Which factors appear significant?",
        "7. Plan a follow-up design with the significant factors",
    ])

    prs.save("slides/Module_04_Screening_Designs.pptx")
    print("  Module 4 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 5
# ═══════════════════════════════════════════════════════════

def build_module_5():
    prs = new_prs()

    add_title_slide(prs,
        "Response Surface\nDesigns",
        "Modeling curved relationships and finding optimal settings",
        module_num=5)

    add_content_slide(prs, "Learning Objectives", [
        "Understand when you need response surface methodology (RSM)",
        "Learn Central Composite Design (CCD) and Box-Behnken",
        "Use Latin Hypercube Sampling for space-filling",
        "Generate RSM designs with doe-helper",
        "Interpret 3D surface plots and contour plots",
        "Use doe optimize to find optimal factor settings",
    ])

    add_content_slide(prs, "When to Move Beyond Screening", [
        "Screening identified the vital few factors (typically 2\u20134)",
        "Center points showed evidence of curvature",
        "You need to find the optimum, not just know what matters",
        "RSM fits a quadratic model:",
        ">> y = b\u2080 + b\u2081x\u2081 + b\u2082x\u2082 + b\u2081\u2082x\u2081x\u2082 + b\u2081\u2081x\u2081\u00b2 + b\u2082\u2082x\u2082\u00b2",
        "This captures curves, ridges, saddle points, and optima",
    ])

    add_two_col_slide(prs, "CCD vs. Box-Behnken",
        [
            "Central Composite Design (CCD)",
            "",
            "Three components:",
            "  \u2022 2\u1d4f factorial corner points",
            "  \u2022 2k star (axial) points",
            "  \u2022 3\u20136 center point replicates",
            "",
            "3 factors: 8+6+6 = 20 runs",
            "Can be built sequentially",
            "Includes extreme corners",
        ],
        [
            "Box-Behnken Design (BBD)",
            "",
            "Does NOT include corner points",
            "Good when extremes are costly",
            "or dangerous",
            "",
            "3 factors: 15 runs (vs. 20 CCD)",
            "4 factors: 27 runs (vs. 30 CCD)",
            "Slightly less information than CCD",
            "but often sufficient",
        ],
        left_title="CCD",
        right_title="BOX-BEHNKEN"
    )

    add_code_slide(prs, "CCD with doe-helper", """
{
  "factors": {
    "temperature": {"low": 150, "high": 200, "units": "C"},
    "pressure":    {"low": 1.0, "high": 5.0, "units": "bar"},
    "catalyst":    {"low": 0.5, "high": 1.5, "units": "g"}
  },
  "responses": {
    "yield":  {"units": "%", "target": "maximize"},
    "purity": {"units": "%", "target": "maximize"}
  },
  "design": {"type": "ccd", "center_points": 6}
}

$ doe generate reactor_rsm/
$ doe info reactor_rsm/
  Type: ccd  |  Runs: 20  |  Factors: 3
""")

    add_content_slide(prs, "Latin Hypercube Sampling & Design Selection", [
        "LHS: space-filling design, not model-based",
        ">> Samples spread evenly across the entire factor space",
        ">> Good for computer experiments and simulations",
        ">> doe-helper: \"type\": \"latin_hypercube\", \"runs\": N",
        "",
        "Design selection guide:",
        ">> 2\u20133 factors, need optimum \u2192 CCD or Box-Behnken",
        ">> Avoid extreme corners \u2192 Box-Behnken",
        ">> Unknown model, simulation \u2192 Latin Hypercube",
        ">> Constrained factor space \u2192 D-Optimal",
    ])

    add_code_slide(prs, "Optimization with doe-helper", """
$ doe optimize reactor_rsm/

Optimization Results
  Method: L-BFGS-B with 20 random restarts

  Optimal Settings:
    temperature: 182.3 C
    pressure:    3.8 bar
    catalyst:    1.2 g

  Predicted Responses:
    yield:  94.2%  (target: maximize)
    purity: 98.7%  (target: maximize)

  Desirability: 0.93
""", "doe optimize uses scipy.optimize with multi-start for global search")

    add_content_slide(prs, "Steepest Ascent / Descent", [
        "Sequential experimentation strategy:",
        ">> Start with factorial near current operating settings",
        ">> Fit a linear model to identify the steepest ascent direction",
        ">> Run experiments along this path until response plateaus",
        ">> Run a new RSM design at the plateau",
        "doe-helper computes the steepest ascent path automatically",
        "Efficient when you're far from the optimum",
    ])

    add_key_point_slide(prs, "Key Takeaways", [
        "RSM fits quadratic models to find optima",
        "CCD is the workhorse; Box-Behnken avoids extremes",
        "LHS for space-filling when the model is unknown",
        "doe optimize uses L-BFGS-B with multi-start",
        "Steepest ascent helps when you're far from the optimum",
    ])

    add_exercise_slide(prs, "Exercise 5: Response Surface Optimisation", [
        "1. Create a reactor experiment with 3 factors, type \"ccd\"",
        "2. Run:  doe generate reactor_rsm/",
        ">> How many runs? What's the structure?",
        "3. Run the simulation:  bash reactor_rsm/run.sh",
        "4. Run:  doe analyze reactor_rsm/",
        ">> Look at the response surface plots",
        "5. Run:  doe optimize reactor_rsm/",
        ">> What are the recommended optimal settings?",
        "6. Try Box-Behnken: change type, repeat",
        ">> Compare run count and optimal settings",
    ])

    prs.save("slides/Module_05_Response_Surface.pptx")
    print("  Module 5 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 6
# ═══════════════════════════════════════════════════════════

def build_module_6():
    prs = new_prs()

    add_title_slide(prs,
        "Analysis and\nInterpretation",
        "Turning experimental data into actionable insights",
        module_num=6)

    add_content_slide(prs, "Learning Objectives", [
        "Read and interpret ANOVA tables confidently",
        "Use Pareto charts and main-effects plots",
        "Understand residual analysis and model diagnostics",
        "Detect and handle model inadequacy",
        "Use doe analyze for automated analysis",
        "Generate comprehensive HTML reports with doe report",
    ])

    add_content_slide(prs, "The doe analyze Output", [
        "doe analyze produces a complete analysis package:",
        ">> ANOVA table with F-tests and p-values",
        ">> Effect estimates with 95% confidence intervals",
        ">> Pareto chart of effect magnitudes",
        ">> Main effects plots and interaction plots",
        ">> Normal probability plot of effects",
        ">> Residual diagnostics (4-panel plot)",
        ">> Model summary (R\u00b2, adjusted R\u00b2, predicted R\u00b2)",
    ])

    add_content_slide(prs, "ANOVA Table Deep Dive", [
        "SS (Sum of Squares) \u2014 total variability explained",
        ">> % Contribution = SS_source / SS_total \u00d7 100",
        "DF (Degrees of Freedom) \u2014 parameters used",
        "MS (Mean Square) \u2014 SS / DF",
        "F-value \u2014 MS_source / MS_error (signal-to-noise ratio)",
        "p-value \u2014 probability of seeing this F by chance",
        ">> p < 0.05: significant   |   p < 0.01: highly significant",
    ])

    add_two_col_slide(prs, "Main Effects & Interaction Plots",
        [
            "Main Effects Plot:",
            "Shows average response at each level",
            "Steep slope = large effect",
            "Flat line = no effect",
            "Quick visual scan of what matters",
        ],
        [
            "Interaction Plot:",
            "Response for each factor combination",
            "Parallel lines = no interaction",
            "Non-parallel / crossing = interaction",
            "OVAT misses these completely",
        ],
        left_title="MAIN EFFECTS",
        right_title="INTERACTIONS"
    )

    add_content_slide(prs, "Normal Probability Plot of Effects", [
        "Plots effect estimates vs. expected normal quantiles",
        "Inactive effects fall on a straight line through zero",
        "Active effects deviate from the line",
        "Particularly useful for unreplicated designs",
        ">> No error estimate available \u2192 use this visual method",
        "doe-helper generates both normal and half-normal plots",
    ])

    add_content_slide(prs, "Residual Diagnostics (4-Panel Plot)", [
        "1. Residuals vs. Fitted \u2014 check for patterns (should be random)",
        ">> Funnel shape \u2192 non-constant variance (transform response)",
        ">> Curve \u2192 missing quadratic terms (need RSM)",
        "2. Normal Q-Q \u2014 residuals should follow normal distribution",
        "3. Residuals vs. Run Order \u2014 check for time trends",
        "4. Residuals Histogram \u2014 should be roughly bell-shaped",
        "Patterns in residuals signal model problems",
    ])

    add_content_slide(prs, "Model Adequacy Statistics", [
        "R\u00b2 \u2014 fraction of variability explained (R\u00b2 > 0.9 is good)",
        "Adjusted R\u00b2 \u2014 penalised for number of terms",
        ">> Should be close to R\u00b2 (big gap = overfitting)",
        "Predicted R\u00b2 (PRESS) \u2014 cross-validation metric",
        ">> Should agree with Adj R\u00b2 within ~0.2",
        "Lack-of-Fit test \u2014 is the model adequate?",
        ">> Significant LOF \u2192 model is missing important terms",
    ])

    add_code_slide(prs, "doe analyze in Practice", """
$ doe analyze reactor_rsm/

ANOVA Table
  Source        SS       DF    MS       F       p-value  Sig
  temperature   1240.5   1    1240.5   45.2    0.0001   ***
  pressure       890.3   1     890.3   32.4    0.0005   ***
  catalyst        45.2   1      45.2    1.6    0.2345
  temp*press     320.1   1     320.1   11.7    0.0089   **
  temp^2         156.7   1     156.7    5.7    0.0412   *

Model: R^2 = 0.967   Adj R^2 = 0.945   Pred R^2 = 0.912
""")

    add_code_slide(prs, "Generating HTML Reports", """
$ doe report reactor_rsm/
  Report generated: reactor_rsm/report.html

# The report includes:
#   - Executive summary with key findings
#   - Interactive plots (zoom, hover, pan)
#   - Full ANOVA table
#   - Effect estimates and confidence intervals
#   - Residual diagnostics
#   - Response surface plots (for RSM designs)
#   - Optimal settings (if doe optimize was run)
#   - Self-contained single HTML file (easy to share)
""")

    add_key_point_slide(prs, "Key Takeaways", [
        "doe analyze automates the entire analysis pipeline",
        "Pareto chart: quick visual ID of significant factors",
        "Always check residual plots for model adequacy",
        "R\u00b2, Adj-R\u00b2, and Pred-R\u00b2 should be close and high",
        "doe report creates shareable HTML reports with all results",
    ])

    add_exercise_slide(prs, "Exercise 6: Analyse and Interpret", [
        "Use the reactor experiment from Exercise 5.",
        "",
        "1. Run:  doe analyze reactor_rsm/",
        "2. ANOVA: which factors are significant at p < 0.05?",
        "3. Pareto chart: do the results agree with ANOVA?",
        "4. Residual diagnostics:",
        ">> Any patterns in residuals vs. fitted?",
        ">> Do residuals follow a normal distribution?",
        "5. Run:  doe report reactor_rsm/",
        "6. Write a 3-sentence executive summary",
    ])

    prs.save("slides/Module_06_Analysis.pptx")
    print("  Module 6 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 7
# ═══════════════════════════════════════════════════════════

def build_module_7():
    prs = new_prs()

    add_title_slide(prs,
        "Multi-Response Optimisation\n& Advanced Topics",
        "Balancing competing objectives and extending designs",
        module_num=7)

    add_content_slide(prs, "Learning Objectives", [
        "Optimise for multiple responses simultaneously",
        "Understand desirability functions",
        "Use design augmentation strategies",
        "Apply blocking and randomisation correctly",
        "Use Taguchi designs for robust parameter design",
        "Handle mixture experiments",
    ])

    add_content_slide(prs, "Multi-Response Optimisation", [
        "Most real experiments have multiple responses",
        ">> Maximise yield AND minimise cost",
        ">> Minimise latency AND maximise throughput",
        "Responses often conflict: improving one degrades another",
        "Derringer-Suich desirability function:",
        ">> Transform each response to a 0\u20131 desirability scale",
        ">> Overall D = geometric mean of individual d\u1d62",
        ">> D = 1: perfect  |  D = 0: unacceptable",
    ])

    add_code_slide(prs, "Multi-Response Config & Optimization", """
{
  "responses": {
    "yield":  {"units": "%",   "target": "maximize"},
    "cost":   {"units": "USD", "target": "minimize"},
    "purity": {"units": "%",   "target": 99.5}
  }
}

$ doe optimize reactor_multi/

Optimization Results:
  yield=91.2%, cost=$42.30, purity=99.3%
  Overall desirability: 0.87
""", "doe optimize balances all responses via desirability functions")

    add_content_slide(prs, "Design Augmentation", [
        "Often you want to extend an existing design",
        "doe augment supports several strategies:",
        ">> Fold-over: mirror design to break aliases",
        ">> Star points: add axial points for RSM",
        ">> Center points: add runs at the center",
        "Benefits:",
        ">> Leverages data you already have",
        ">> Sequentially builds up information",
        ">> No need to start over from scratch",
    ])

    add_two_col_slide(prs, "Taguchi & Mixture Designs",
        [
            "Taguchi Designs",
            "Focus on robustness to noise",
            "Inner array: controllable factors",
            "Outer array: noise factors",
            "S/N ratio as the response",
            "doe-helper: \"type\": \"taguchi\"",
        ],
        [
            "Mixture Experiments",
            "Proportions must sum to 1",
            "E.g. concrete, alloys, formulations",
            "Simplex-Lattice: evenly spaced",
            "Simplex-Centroid: vertices + center",
            "doe-helper: \"type\": \"simplex_lattice\"",
        ],
        left_title="ROBUST DESIGN",
        right_title="MIXTURES"
    )

    add_content_slide(prs, "Blocking & D-Optimal Designs", [
        "Blocking accounts for known nuisance variables",
        ">> Different batches, days, operators, machines",
        ">> Block effects are estimated and removed from analysis",
        ">> doe-helper: set \"blocks\" in the design section",
        "",
        "D-Optimal: computer-generated for non-standard situations",
        ">> Irregular factor space, constraints",
        ">> Mix of continuous and categorical factors",
        ">> doe-helper: \"type\": \"d_optimal\", \"runs\": N",
    ])

    add_code_slide(prs, "Power Analysis with doe-helper", """
$ doe power experiment/

Power Analysis
  Design:       full_factorial (2^3)
  Runs:         8
  Error est.:   2.5 (from prior data or estimate)

  Detectable Effect Sizes (80% power, alpha=0.05):
    Main effects:    3.2 units
    2-factor int.:   3.2 units

$ doe power experiment/ --effect-size 5.0
  Power: 0.95 for main effects
  Power: 0.95 for 2-factor interactions
""", "Power analysis ensures your design can detect meaningful effects")

    add_key_point_slide(prs, "Key Takeaways", [
        "Multi-response: desirability functions balance trade-offs",
        "doe augment extends designs without starting over",
        "Blocking removes nuisance variation systematically",
        "Taguchi designs optimise for robustness to noise",
        "D-Optimal handles constraints and irregular spaces",
    ])

    add_exercise_slide(prs, "Exercise 7: Multi-Response Optimisation", [
        "1. Add 3 responses to the reactor experiment:",
        ">> yield (maximize), cost (minimize), purity (target: 99.5)",
        "2. Run:  doe optimize reactor_multi/",
        ">> What is the overall desirability score?",
        ">> Which response is most compromised?",
        "3. Run:  doe power reactor_multi/",
        ">> Is the design adequately powered?",
        "4. Try:  doe augment reactor_multi/ --method center-points --count 4",
        ">> How does augmentation change the power analysis?",
    ])

    prs.save("slides/Module_07_Advanced_Topics.pptx")
    print("  Module 7 saved")


# ═══════════════════════════════════════════════════════════
# MODULE 8
# ═══════════════════════════════════════════════════════════

def build_module_8():
    prs = new_prs()

    add_title_slide(prs,
        "Capstone Project",
        "Apply the full DOE workflow to a real-world problem",
        module_num=8)

    add_content_slide(prs, "Capstone Overview", [
        "Apply everything you've learned in one complete project",
        "Choose from three scenario options or propose your own",
        "Complete the full DOE workflow:",
        ">> 1. Problem definition and factor selection",
        ">> 2. Screening design",
        ">> 3. Follow-up design (factorial or RSM)",
        ">> 4. Analysis and interpretation",
        ">> 5. Optimisation",
        ">> 6. Final report",
    ])

    add_two_col_slide(prs, "Option A: Cloud Infrastructure",
        [
            "Optimise a Kubernetes microservice",
            "",
            "10 candidate factors:",
            "CPU limit, memory limit, replicas,",
            "connection pool, thread count,",
            "cache TTL, batch size, retry limit,",
            "timeout, GC interval",
        ],
        [
            "3 responses:",
            "p99 latency (minimize)",
            "throughput (maximize)",
            "cost per hour (minimize)",
            "",
            "Budget: 40 total runs",
            "across all phases",
        ],
        left_title="FACTORS",
        right_title="OBJECTIVES"
    )

    add_two_col_slide(prs, "Option B: 3D Printing  |  Option C: Bread Baking",
        [
            "3D Printing",
            "8 factors: layer height, speed,",
            "nozzle temp, bed temp, infill %,",
            "retraction, cooling, wall count",
            "",
            "3 responses: tensile strength (max),",
            "print time (min), surface quality (max)",
            "Budget: 30 runs",
        ],
        [
            "Bread Baking",
            "7 factors: flour protein %, hydration,",
            "starter %, salt %, bulk ferment,",
            "proof time, oven temperature",
            "",
            "3 responses: loaf volume (max),",
            "crumb score (max), crust color (target: 4)",
            "Budget: 25 runs",
        ],
        left_title="OPTION B",
        right_title="OPTION C"
    )

    add_content_slide(prs, "Capstone Requirements", [
        "Phase 1: Screening  (~30 min)",
        ">> Choose PB or DSD for all candidate factors",
        ">> Identify the 3\u20134 most important factors",
        ">> Document reasoning for dropping factors",
        "",
        "Phase 2: RSM & Optimisation  (~30 min)",
        ">> Run CCD or Box-Behnken on surviving factors",
        ">> Analyse with doe analyze, interpret the surface",
        ">> Optimise with doe optimize",
    ])

    add_content_slide(prs, "Capstone Deliverables", [
        "1. config.json files for screening and RSM phases",
        "2. doe report HTML output for each phase",
        "3. Summary document (1\u20132 pages):",
        ">> Problem statement and factor selection rationale",
        ">> Screening results and factor elimination decisions",
        ">> RSM analysis and optimal settings",
        ">> Practical recommendations",
        "4. Brief presentation (5 minutes) to the class",
    ])

    add_code_slide(prs, "Capstone Workflow with doe-helper", """
# Phase 1: Screening
$ doe init project/ --design plackett_burman
$ doe generate project/ && bash project/run.sh
$ doe analyze project/

# Phase 2: RSM (with reduced factors)
$ doe generate project_rsm/ && bash project_rsm/run.sh
$ doe analyze project_rsm/

# Phase 3: Optimise & Report
$ doe optimize project_rsm/
$ doe report project_rsm/
""")

    add_exercise_slide(prs, "Capstone Project", [
        "1. Choose Option A, B, C, or propose your own",
        "2. Complete the full workflow using doe-helper",
        "3. Produce all deliverables from the previous slide",
        "4. Prepare a 5-minute presentation:",
        ">> What you learned about the system",
        ">> Key factors and their effects",
        ">> Optimal settings and predicted performance",
        ">> What you would do next with more runs",
        "",
        "Time: 70 min project + 20 min presentations",
    ])

    add_section_divider(prs, "Course Summary",
        "Congratulations on completing the DOE Helper Training Course!")

    add_content_slide(prs, "What You've Learned", [
        "Module 1: Why DOE matters and the OVAT trap",
        "Module 2: doe-helper installation and configuration",
        "Module 3: Full factorial designs and interactions",
        "Module 4: Screening designs for many factors",
        "Module 5: Response surface methodology and optimisation",
        "Module 6: Analysis, interpretation, and reporting",
        "Module 7: Multi-response optimisation and advanced topics",
        "Module 8: Complete DOE workflow from problem to solution",
    ])

    add_content_slide(prs, "doe-helper Command Reference", [
        "doe init             Create experiment from template",
        "doe generate         Create design matrix and runner script",
        "doe record           Interactively record results",
        "doe status           Show experiment progress",
        "doe info             Display design summary and metrics",
        "doe analyze          Run ANOVA, effects, diagnostics, plots",
        "doe optimize         Find optimal factor settings",
        "doe power            Compute statistical power",
        "doe augment          Extend an existing design",
        "doe report           Generate interactive HTML report",
    ])

    add_key_point_slide(prs, "Next Steps", [
        "Practice with the 221 built-in use cases",
        "Visit doehelper.com for documentation and examples",
        "Apply DOE to a real problem in your work",
        "Start small: 2\u20133 factors, full factorial",
        "A planned experiment beats trial-and-error every time",
    ])

    prs.save("slides/Module_08_Capstone.pptx")
    print("  Module 8 saved")


# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating DOE Helper Training Course slides...")
    build_module_1()
    build_module_2()
    build_module_3()
    build_module_4()
    build_module_5()
    build_module_6()
    build_module_7()
    build_module_8()
    print("\nAll 8 modules saved to training/slides/")
