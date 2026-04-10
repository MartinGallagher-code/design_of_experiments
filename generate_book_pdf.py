#!/usr/bin/env python3
"""Generate a Crown Quarto (7.44×9.68 inch) PDF book suitable for Lulu.com from the DOE Helper website content.

Combines:
  Part I   – Introduction (new)
  Part II  – User's Guide (from guide.html)
  Part III – Technical Reference (from reference.html)
  Part IV  – Design of Experiments Theory (from book.html)

Usage:
    python generate_book_pdf.py
"""

import re
from pathlib import Path
from html.parser import HTMLParser


WEBSITE = Path(__file__).parent / "website"
OUTPUT  = Path(__file__).parent / "doe_helper_book.pdf"


# ──────────────────────────────────────────────
# HTML content extraction helpers
# ──────────────────────────────────────────────

def read_file(name: str) -> str:
    return (WEBSITE / name).read_text(encoding="utf-8")


def extract_between(html: str, start_pattern: str, end_pattern: str) -> str:
    """Extract HTML between two regex patterns (inclusive of start, exclusive of end)."""
    m_start = re.search(start_pattern, html)
    m_end = re.search(end_pattern, html[m_start.end():]) if m_start else None
    if not m_start:
        return ""
    if m_end:
        return html[m_start.start(): m_start.end() + m_end.start()]
    return html[m_start.start():]


def extract_body_content(html: str, start_marker: str, end_marker: str | None = None) -> str:
    """Extract content from body between markers."""
    start = html.find(start_marker)
    if start == -1:
        return ""
    if end_marker:
        end = html.find(end_marker, start + len(start_marker))
        if end == -1:
            end = html.find("</body>", start)
        return html[start:end]
    else:
        end = html.find("</body>", start)
        return html[start:end] if end != -1 else html[start:]


def strip_nav_and_chrome(html: str) -> str:
    """Remove nav, hero, footer, sidebar, scripts, style blocks from extracted content."""
    # Remove <nav> blocks
    html = re.sub(r'<nav\b[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    # Remove <footer> blocks
    html = re.sub(r'<footer\b[^>]*>.*?</footer>', '', html, flags=re.DOTALL)
    # Remove sidebar
    html = re.sub(r'<aside\b[^>]*>.*?</aside>', '', html, flags=re.DOTALL)
    # Remove mobile TOC
    html = re.sub(r'<nav class="mobile-toc"[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    html = re.sub(r'<nav class="mobile-toc"[^>]*></nav>', '', html, flags=re.DOTALL)
    # Remove script tags
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    # Remove button.sidebar-toggle
    html = re.sub(r'<button class="sidebar-toggle"[^>]*>.*?</button>', '', html, flags=re.DOTALL)
    # Remove code-copy buttons
    html = re.sub(r'<button class="code-copy"[^>]*>.*?</button>', '', html, flags=re.DOTALL)
    # Remove chapter-nav divs (prev/next links)
    html = re.sub(r'<div class="chapter-nav">.*?</div>', '', html, flags=re.DOTALL)
    # Remove hero sections
    html = re.sub(r'<section class="howto-hero"[^>]*>.*?</section>', '', html, flags=re.DOTALL)
    html = re.sub(r'<section class="ref-hero"[^>]*>.*?</section>', '', html, flags=re.DOTALL)
    html = re.sub(r'<section class="book-cover"[^>]*>.*?</section>', '', html, flags=re.DOTALL)
    # Remove bg-logo images
    html = re.sub(r'<img[^>]*class="bg-logo[^"]*"[^>]*>', '', html)
    # Remove abstract-deco div
    html = re.sub(r'<div class="abstract-deco"[^>]*>.*?</div>\s*</div>\s*</div>\s*</div>', '', html, flags=re.DOTALL)
    # Remove TOC section (guide.html)
    html = re.sub(r'<section class="howto-section" id="toc">.*?</section>', '', html, flags=re.DOTALL)
    # Remove step badges
    html = re.sub(r'<span class="step-badge">\d+</span>\s*', '', html)
    # Clean up empty divs
    html = re.sub(r'<div class="home-inner">\s*<div class="hero-left">.*?</div>\s*</div>', '', html, flags=re.DOTALL)
    return html


def extract_guide_content() -> str:
    """Extract the User's Guide content from guide.html."""
    html = read_file("guide.html")
    # Get everything from first howto-section to footer
    sections = re.findall(r'<section class="howto-section"[^>]*>.*?</section>', html, re.DOTALL)
    content = "\n\n".join(sections)
    content = strip_nav_and_chrome(content)
    # Remove the TOC section
    content = re.sub(r'<section class="howto-section" id="toc">.*?</section>', '', content, flags=re.DOTALL)
    return content


def extract_reference_content() -> str:
    """Extract the Technical Reference content from reference.html."""
    html = read_file("reference.html")
    # Get content inside book-content main
    m = re.search(r'<main class="book-content">(.*?)</main>', html, re.DOTALL)
    if m:
        content = m.group(1)
    else:
        content = extract_body_content(html, '<section id="cli">', '</body>')
    content = strip_nav_and_chrome(content)
    return content


def extract_book_content() -> str:
    """Extract the DOE Theory book content from book.html."""
    html = read_file("book.html")
    # Get content inside book-content main
    m = re.search(r'<main class="book-content">(.*?)</main>', html, re.DOTALL)
    if m:
        content = m.group(1)
    else:
        content = ""
    content = strip_nav_and_chrome(content)
    # Remove the User Guide section (it's just links to guide.html/reference.html)
    content = re.sub(r'<section id="user-guide">.*?</section>', '', content, flags=re.DOTALL)
    return content


# ──────────────────────────────────────────────
# Build the complete book HTML
# ──────────────────────────────────────────────

def build_book_html() -> str:
    guide = extract_guide_content()
    reference = extract_reference_content()
    theory = extract_book_content()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DOE Helper — Design Experiments, Not Guesswork</title>
<style>
/* ── Page setup: Crown Quarto (7.44×9.68 inch) for Lulu.com ── */
@page {{
  size: 7.44in 9.68in;
  margin: 0.75in 0.75in 0.875in 0.75in;  /* top right bottom left */
  @bottom-center {{
    content: counter(page);
    font: 9pt "Inter", sans-serif;
    color: #666;
  }}
}}
@page :first {{
  @bottom-center {{ content: none; }}
}}
@page :blank {{
  @bottom-center {{ content: none; }}
}}

/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Base ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 10pt; }}
body {{
  font: 400 10pt/1.55 'Merriweather', Georgia, serif;
  color: #222;
  orphans: 3;
  widows: 3;
}}
a {{ color: #333; text-decoration: none; }}
img, svg {{ max-width: 100%; height: auto; }}

/* ── Headings ── */
h1, h2, h3, h4 {{
  font-family: 'Inter', system-ui, sans-serif;
  page-break-after: avoid;
  break-after: avoid;
  color: #111;
}}
h1 {{
  font-size: 20pt;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0 0 8pt;
  line-height: 1.15;
}}
h2 {{
  font-size: 14pt;
  font-weight: 700;
  margin: 24pt 0 8pt;
  padding-bottom: 3pt;
  border-bottom: 1.5pt solid #ddd;
  letter-spacing: -0.02em;
}}
h3 {{
  font-size: 11pt;
  font-weight: 600;
  color: #4338ca;
  margin: 16pt 0 6pt;
}}
h4 {{
  font-size: 10pt;
  font-weight: 600;
  margin: 12pt 0 4pt;
}}

/* ── Paragraphs & lists ── */
p {{
  margin: 0 0 8pt;
  font-size: 10pt;
  line-height: 1.55;
}}
ul, ol {{
  margin: 0 0 8pt 14pt;
  font-size: 10pt;
}}
li {{
  margin-bottom: 2pt;
  line-height: 1.5;
}}
strong {{ font-weight: 700; }}
em {{ font-style: italic; }}

/* ── Code ── */
code {{
  font: 500 9pt/1.4 'JetBrains Mono', 'Consolas', monospace;
  background: #f3f4f6;
  padding: 0.5pt 3pt;
  border-radius: 2pt;
  word-break: break-all;
}}
pre {{
  margin: 6pt 0 10pt;
  page-break-inside: avoid;
  break-inside: avoid;
}}
pre code {{
  display: block;
  background: #1a1a2e;
  color: #d4d4d4;
  padding: 10pt 12pt;
  border-radius: 4pt;
  font-size: 8.5pt;
  line-height: 1.55;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  word-break: break-all;
}}

/* ── Code blocks (website style) ── */
.code-block {{
  background: #1a1a2e;
  border-radius: 4pt;
  margin: 6pt 0 10pt;
  page-break-inside: avoid;
  break-inside: avoid;
  overflow: hidden;
}}
.code-header {{
  background: #252540;
  padding: 5pt 12pt;
  font: 500 7.5pt 'JetBrains Mono', monospace;
  color: #888;
}}
.code-body {{
  padding: 10pt 12pt;
  font: 400 8.5pt/1.55 'JetBrains Mono', monospace;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}}
.code-body .prompt {{ color: #6ec86e; }}
.code-body .flag {{ color: #8b9cf7; }}
.code-body .string {{ color: #e5a64e; }}
.code-body .key {{ color: #5cc8d8; }}
.code-body .comment {{ color: #777; }}
.code-body .number {{ color: #b5cea8; }}

/* ── Tables ── */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 8pt 0 12pt;
  font-size: 9pt;
  page-break-inside: avoid;
  break-inside: avoid;
}}
thead th {{
  background: #1e1b4b;
  color: #fff;
  padding: 6pt 8pt;
  text-align: left;
  font: 600 8pt 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
thead th:first-child {{ border-radius: 3pt 0 0 0; }}
thead th:last-child {{ border-radius: 0 3pt 0 0; }}
tbody td {{
  padding: 6pt 8pt;
  border-bottom: 0.5pt solid #e5e5e5;
  vertical-align: top;
  line-height: 1.45;
}}
tbody tr:nth-child(even) {{ background: #f9fafb; }}

/* flag-table (reference) */
.flag-table {{ font-size: 8.5pt; }}
.flag-table thead th {{
  background: #1e1b4b;
  color: #fff;
  padding: 6pt 8pt;
  font-size: 7.5pt;
}}
.flag-table td {{ padding: 5pt 8pt; font-size: 8.5pt; }}
.cmd-header {{ margin-top: 18pt; margin-bottom: 2pt; }}
.cmd-header code {{ font-size: 11pt; font-weight: 600; color: #4338ca; background: none; }}

/* ── Callout boxes ── */
.callout {{
  border-radius: 4pt;
  padding: 8pt 10pt;
  margin: 8pt 0;
  font-size: 9pt;
  line-height: 1.45;
  page-break-inside: avoid;
  break-inside: avoid;
  display: flex;
  gap: 8pt;
}}
.callout-icon {{ font-size: 11pt; flex-shrink: 0; }}
.callout h4 {{ font-size: 9pt; font-weight: 700; margin-bottom: 2pt; }}
.callout p {{ font-size: 9pt; margin: 0; }}
.callout.info {{ background: #eef2ff; border-left: 2.5pt solid #5046e5; }}
.callout.info h4 {{ color: #5046e5; }}
.callout.success {{ background: #f0fdf4; border-left: 2.5pt solid #16a34a; }}
.callout.success h4 {{ color: #16a34a; }}
.callout.warning {{ background: #fffbeb; border-left: 2.5pt solid #d97706; }}
.callout.warning h4 {{ color: #d97706; }}
.callout.danger {{ background: #fff1f2; border-left: 2.5pt solid #e11d48; }}
.callout.danger h4 {{ color: #e11d48; }}

/* ── Keypoint / analogy / warning boxes ── */
.keypoint-box {{
  background: #eef2ff;
  border: 0.75pt solid #c7d2fe;
  border-radius: 4pt;
  padding: 10pt 12pt;
  margin: 10pt 0;
  page-break-inside: avoid;
  break-inside: avoid;
}}
.keypoint-box h4 {{ font-size: 9pt; font-weight: 700; color: #4338ca; margin-bottom: 3pt; }}
.keypoint-box p {{ font-size: 9pt; color: #3730a3; margin: 0; line-height: 1.45; }}

.analogy {{
  background: #f0fdf4;
  border: 0.75pt solid #86efac;
  border-radius: 4pt;
  padding: 10pt 12pt;
  margin: 10pt 0;
  page-break-inside: avoid;
}}
.analogy h4 {{ font-size: 9pt; font-weight: 700; color: #166534; margin-bottom: 3pt; }}
.analogy p {{ font-size: 9pt; color: #15803d; margin: 0; line-height: 1.45; }}

.warning-box {{
  background: #fffbeb;
  border: 0.75pt solid #fcd34d;
  border-radius: 4pt;
  padding: 10pt 12pt;
  margin: 10pt 0;
  page-break-inside: avoid;
}}
.warning-box h4 {{ font-size: 9pt; font-weight: 700; color: #92400e; margin-bottom: 3pt; }}
.warning-box p {{ font-size: 9pt; color: #a16207; margin: 0; line-height: 1.45; }}

.danger-box {{
  background: #fff1f2;
  border: 0.75pt solid #fca5a5;
  border-radius: 4pt;
  padding: 10pt 12pt;
  margin: 10pt 0;
  page-break-inside: avoid;
}}
.danger-box h4 {{ font-size: 9pt; font-weight: 700; color: #9f1239; margin-bottom: 3pt; }}
.danger-box p {{ font-size: 9pt; color: #be123c; margin: 0; line-height: 1.45; }}

/* ── Math boxes ── */
.math {{
  background: #f5f3ff;
  border: 0.75pt solid #c7d2fe;
  border-radius: 4pt;
  padding: 8pt 10pt;
  margin: 8pt 0;
  font-family: Georgia, serif;
  font-size: 10pt;
  text-align: center;
  page-break-inside: avoid;
}}

/* ── Comparison grid ── */
.comparison-grid {{
  display: flex;
  gap: 8pt;
  margin: 10pt 0;
}}
.comparison-card {{
  flex: 1;
  border-radius: 4pt;
  padding: 10pt;
  font-size: 9pt;
}}
.comparison-card.bad {{ background: #fff1f2; border: 0.5pt solid #fca5a5; }}
.comparison-card.good {{ background: #f0fdf4; border: 0.5pt solid #86efac; }}
.comparison-card h4 {{ font-size: 9pt; margin-bottom: 4pt; }}

/* ── Visual grid ── */
.visual-grid {{
  display: flex;
  flex-wrap: wrap;
  gap: 4pt;
  margin: 8pt 0;
}}
.visual-cell {{
  text-align: center;
  padding: 6pt 4pt;
  border-radius: 3pt;
  font-size: 7.5pt;
  font-weight: 600;
  flex: 1;
  min-width: 60pt;
}}
.progress-bar {{ height: 2pt; background: #e5e5e5; border-radius: 1pt; margin-top: 2pt; overflow: hidden; }}
.progress-bar-fill {{ height: 100%; border-radius: 1pt; }}

/* ── Accordion (print as always-open) ── */
.accordion {{ margin: 8pt 0; }}
.accordion-item {{
  border: 0.5pt solid #e5e5e5;
  border-radius: 4pt;
  margin-bottom: 4pt;
  overflow: hidden;
  page-break-inside: avoid;
}}
.accordion-header {{
  padding: 8pt 10pt;
  font: 600 9.5pt 'Inter', sans-serif;
}}
.accordion-header .arrow {{ display: none; }}
.accordion-body {{
  max-height: none !important;
  padding: 0 10pt 10pt !important;
  overflow: visible !important;
}}
.accordion-item .accordion-body {{ display: block; }}

/* ── Tabs (print all panels) ── */
.tabs {{ display: none; }}
.tab-panel {{ display: block !important; margin-bottom: 8pt; }}

/* ── Workflow diagram ── */
.workflow-diagram {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin: 12pt 0;
}}
.workflow-box {{
  background: #4338ca;
  color: #fff;
  border-radius: 4pt;
  padding: 6pt 10pt;
  text-align: center;
  font: 600 8.5pt 'Inter', sans-serif;
}}
.workflow-box .wf-cmd {{
  display: block;
  font-size: 6.5pt;
  font-weight: 400;
  opacity: .85;
  margin-top: 2pt;
  font-family: 'JetBrains Mono', monospace;
}}
.workflow-arrow {{
  font-size: 11pt;
  color: #999;
  padding: 0 3pt;
}}

/* ── Config anatomy ── */
.config-anatomy {{
  border-left: 2pt solid #4338ca;
  padding-left: 10pt;
  margin: 8pt 0;
}}
.config-anatomy h4 {{ color: #4338ca; margin-bottom: 2pt; font-size: 9pt; }}
.config-anatomy p {{ font-size: 9pt; color: #333; }}

/* ── Responsive grid overrides ── */
.responsive-grid-2, .responsive-grid-3, .responsive-grid-flow {{
  display: flex;
  flex-wrap: wrap;
  gap: 8pt;
}}
.responsive-grid-2 > *, .responsive-grid-3 > * {{ flex: 1; min-width: 40%; }}

/* ── Part title pages ── */
.part-title {{
  page-break-before: always;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 8in;
  text-align: center;
}}
.part-title h1 {{
  font-size: 32pt;
  font-weight: 800;
  color: #1e1b4b;
  margin-bottom: 8pt;
  letter-spacing: -0.03em;
}}
.part-title .part-subtitle {{
  font: 500 13pt 'Inter', sans-serif;
  color: #6366f1;
  letter-spacing: 0.02em;
}}
.part-title .part-number {{
  font: 700 10pt 'JetBrains Mono', monospace;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 12pt;
}}

/* ── Title page ── */
.title-page {{
  page-break-after: always;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 8in;
  text-align: center;
}}
.title-page h1 {{
  font-size: 36pt;
  font-weight: 800;
  color: #1e1b4b;
  margin-bottom: 6pt;
  letter-spacing: -0.03em;
  line-height: 1.1;
}}
.title-page .subtitle {{
  font: 500 14pt 'Inter', sans-serif;
  color: #6366f1;
  margin-bottom: 30pt;
}}
.title-page .author {{
  font: 400 12pt 'Merriweather', Georgia, serif;
  color: #666;
  margin-bottom: 4pt;
}}
.title-page .year {{
  font: 400 10pt 'JetBrains Mono', monospace;
  color: #999;
}}

/* ── Copyright page ── */
.copyright-page {{
  page-break-after: always;
  padding-top: 5in;
  font-size: 8pt;
  color: #888;
  line-height: 1.7;
}}

/* ── TOC ── */
.toc-page {{
  page-break-after: always;
}}
.toc-page h1 {{
  font-size: 20pt;
  margin-bottom: 16pt;
}}
.toc-page .toc-part {{
  font: 700 9pt 'JetBrains Mono', monospace;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 14pt 0 4pt;
}}
.toc-page .toc-entry {{
  font: 400 10pt 'Inter', sans-serif;
  color: #333;
  margin: 3pt 0;
  padding-left: 8pt;
}}
.toc-page .toc-entry.chapter {{
  font-weight: 600;
  padding-left: 0;
  margin: 6pt 0 2pt;
}}

/* ── Chapter subtitle ── */
.chapter-subtitle {{
  font: 500 10pt 'JetBrains Mono', monospace;
  color: #6366f1;
  margin-bottom: 12pt;
}}

/* ── Lead paragraph ── */
.lead {{
  font-size: 10.5pt;
  color: #555;
  font-style: italic;
  margin-bottom: 12pt;
  line-height: 1.6;
  border-left: 2.5pt solid #6366f1;
  padding-left: 10pt;
}}

/* ── Section breaks ── */
section {{
  page-break-before: always;
}}
section:first-child {{
  page-break-before: auto;
}}

/* ── Howto sections (from guide) ── */
.howto-section {{
  page-break-before: auto;
  padding: 0;
  border: none;
}}

/* ── Miscellaneous website cleanup ── */
.container-narrow {{ max-width: none; }}
.book-content {{ padding: 0; }}
.home, .home-inner, .hero-left, .features, .feature-grid, .feature-card {{
  display: none;
}}

/* ── Horizontal rules ── */
hr {{
  border: none;
  border-top: 0.5pt solid #ddd;
  margin: 16pt 0;
}}

/* ── Sup/sub ── */
sup {{ font-size: 7pt; vertical-align: super; }}
sub {{ font-size: 7pt; vertical-align: sub; }}

/* ── Hidden elements ── */
.nav, .footer, .bg-logo, .bg-logo-light,
.abstract-deco, .nav-toggle, .sidebar-toggle,
.mobile-toc {{ display: none !important; }}

/* ── Print-specific ── */
@media print {{
  body {{ font-size: 10pt; }}
  .part-title {{ height: 100vh; }}
  .title-page {{ height: 100vh; }}
}}
</style>
</head>
<body>

<!-- ══════════════════════════════════════════
     TITLE PAGE
     ══════════════════════════════════════════ -->
<div class="title-page">
  <h1>DOE Helper</h1>
  <div class="subtitle">Design Experiments, Not Guesswork</div>
  <div class="author">Martin J. Gallagher</div>
  <div class="year">2026</div>
</div>

<!-- ══════════════════════════════════════════
     COPYRIGHT PAGE
     ══════════════════════════════════════════ -->
<div class="copyright-page">
  <p><strong>DOE Helper: Design Experiments, Not Guesswork</strong></p>
  <p>Copyright &copy; 2026 Martin J. Gallagher</p>
  <p>Licensed under the GNU General Public License v3.0 or later.</p>
  <p>Published with Lulu.com</p>
  <p style="margin-top: 12pt;">
    This book accompanies the <code>doehelper</code> Python package, available on PyPI.<br>
    Website: doehelper.com
  </p>
  <p style="margin-top: 12pt;">
    No part of this publication may be reproduced without the prior written
    permission of the author, except as permitted under the GPL-3.0 license.
  </p>
  <p style="margin-top: 12pt;">First edition, 2026.</p>
</div>

<!-- ══════════════════════════════════════════
     TABLE OF CONTENTS
     ══════════════════════════════════════════ -->
<div class="toc-page">
  <h1>Contents</h1>

  <div class="toc-part">Part I: Introduction</div>
  <div class="toc-entry chapter">What Is DOE Helper?</div>
  <div class="toc-entry">Why Design of Experiments</div>
  <div class="toc-entry">Who This Book Is For</div>
  <div class="toc-entry">How to Read This Book</div>

  <div class="toc-part">Part II: User&rsquo;s Guide</div>
  <div class="toc-entry chapter">1. Getting Started</div>
  <div class="toc-entry chapter">2. Core Workflow</div>
  <div class="toc-entry chapter">3. Working with Configurations</div>
  <div class="toc-entry chapter">4. Choosing a Design</div>
  <div class="toc-entry chapter">5. Running Experiments</div>
  <div class="toc-entry chapter">6. Analyzing Results</div>
  <div class="toc-entry chapter">7. Optimization</div>
  <div class="toc-entry chapter">8. Advanced Features</div>
  <div class="toc-entry chapter">9. Best Practices</div>
  <div class="toc-entry chapter">10. Troubleshooting</div>

  <div class="toc-part">Part III: Technical Reference</div>
  <div class="toc-entry chapter">CLI Reference</div>
  <div class="toc-entry chapter">Configuration Schema</div>
  <div class="toc-entry chapter">Design Types</div>
  <div class="toc-entry chapter">Analysis Output</div>
  <div class="toc-entry chapter">Output Formats</div>
  <div class="toc-entry chapter">Statistical Formulas</div>
  <div class="toc-entry chapter">Design Evaluation Metrics</div>

  <div class="toc-part">Part IV: Design of Experiments &mdash; Theory</div>
  <div class="toc-entry chapter">Preface</div>
  <div class="toc-entry chapter">Chapter 1: Why Design of Experiments?</div>
  <div class="toc-entry chapter">Chapter 2: Statistical Foundations</div>
  <div class="toc-entry chapter">Chapter 3: Full Factorial Designs</div>
  <div class="toc-entry chapter">Chapter 4: Fractional Factorial Designs</div>
  <div class="toc-entry chapter">Chapter 5: Screening Designs</div>
  <div class="toc-entry chapter">Chapter 6: Response Surface Designs</div>
  <div class="toc-entry chapter">Chapter 7: Analyzing Results</div>
  <div class="toc-entry chapter">Chapter 8: Response Surface Methodology</div>
  <div class="toc-entry chapter">Chapter 9: Practical Troubleshooting</div>
</div>

<!-- ══════════════════════════════════════════
     PART I: INTRODUCTION
     ══════════════════════════════════════════ -->
<div class="part-title">
  <div class="part-number">Part I</div>
  <h1>Introduction</h1>
  <div class="part-subtitle">What This Book Covers and How to Use It</div>
</div>

<section>
<h1>What Is DOE Helper?</h1>

<p><strong>DOE Helper</strong> is a command-line tool that automates the design, execution, and
analysis of scientific experiments using Design of Experiments (DOE) methodology. You
describe your factors and responses in a JSON configuration file, and the tool does
the rest: it picks the optimal experiment plan, generates executable scripts to run
each test, collects the results, and delivers a full statistical analysis &mdash;
complete with ANOVA tables, Pareto charts, response surface models, and optimization
recommendations.</p>

<p>Instead of guessing which settings to try or exhaustively testing every possible
combination, DOE Helper uses mathematically optimal designs to extract the maximum
information from the minimum number of experimental runs. The result is faster
answers, lower costs, and statistically defensible conclusions.</p>

<h2>Why Design of Experiments?</h2>

<p>Every experiment costs something &mdash; time, money, compute cycles, materials.
Poorly planned experiments waste these resources and can lead to wrong conclusions.
The traditional approach of changing one variable at a time (OVAT) misses interactions
between factors and requires far more runs than necessary.</p>

<p>Design of Experiments is a systematic method developed by Ronald Fisher in the 1920s
and refined over the past century for industrial, scientific, and engineering applications.
It lets you:</p>

<ul>
  <li><strong>Test multiple factors simultaneously</strong> &mdash; finding interactions
      that OVAT misses</li>
  <li><strong>Minimize the number of experimental runs</strong> &mdash; a fractional
      factorial can test 7 factors in just 8 runs</li>
  <li><strong>Quantify which factors matter</strong> &mdash; with p-values and
      confidence intervals, not gut feeling</li>
  <li><strong>Find optimal settings</strong> &mdash; using response surface models
      and multi-objective optimization</li>
  <li><strong>Make defensible decisions</strong> &mdash; with statistical power
      analysis and model diagnostics</li>
</ul>

<h2>Who This Book Is For</h2>

<p>This book is written for anyone who runs experiments and wants to do so more
efficiently:</p>

<ul>
  <li><strong>Engineers</strong> optimizing systems, processes, or software configurations</li>
  <li><strong>Scientists</strong> planning laboratory or field experiments</li>
  <li><strong>Data scientists</strong> evaluating model hyperparameters</li>
  <li><strong>Quality engineers</strong> improving manufacturing processes</li>
  <li><strong>DevOps and SRE teams</strong> tuning infrastructure performance</li>
  <li>Anyone who has ever wondered: <em>&ldquo;Which of these 10 knobs actually
      matters?&rdquo;</em></li>
</ul>

<p><strong>Prerequisites:</strong> Basic familiarity with mean, variance, and standard
deviation. No prior statistics coursework is assumed. The tool handles the math; this
book explains how to interpret the results.</p>

<h2>How to Read This Book</h2>

<p>This book has four parts, each designed to stand alone:</p>

<p><strong>Part I (this section)</strong> introduces the tool and sets the stage.</p>

<p><strong>Part II: User&rsquo;s Guide</strong> is a hands-on walkthrough of every feature.
Start here if you want to get running immediately. It covers the complete workflow from
writing your first configuration file through analyzing results and finding optimal
settings.</p>

<p><strong>Part III: Technical Reference</strong> is the authoritative specification.
Every CLI command, every configuration field, every design type algorithm, every formula.
Use this when you need the exact syntax or want to understand what the tool is computing
under the hood.</p>

<p><strong>Part IV: Theory</strong> teaches the statistical foundations of DOE. It covers
factorial designs, fractional factorials, screening designs, response surface methodology,
ANOVA, and practical troubleshooting. Read this to understand <em>why</em> the designs
work, not just <em>how</em> to use them.</p>

<div class="keypoint-box">
  <h4>Suggested Reading Paths</h4>
  <p><strong>New to DOE and the tool:</strong> Read Part I, then Part II (User&rsquo;s Guide),
  then Part IV chapters 1&ndash;3 for theory. Come back to the rest as needed.</p>
  <p style="margin-top: 4pt;"><strong>Know DOE, new to the tool:</strong> Skim Part I,
  then read Part II and keep Part III open as a reference.</p>
  <p style="margin-top: 4pt;"><strong>Already using the tool:</strong> Jump straight to
  Part III for the reference, or Part IV for deeper statistical understanding.</p>
</div>

<h2>What&rsquo;s Included</h2>

<p>The DOE Helper tool supports:</p>

<ul>
  <li><strong>13 design types</strong> &mdash; full factorial, fractional factorial,
      Plackett-Burman, Box-Behnken, central composite, Latin hypercube, definitive
      screening, Taguchi, D-optimal, two mixture designs, and linear/log sweeps</li>
  <li><strong>13 CLI commands</strong> &mdash; generate, analyze, optimize, report,
      info, power, augment, record, status, init, export-worksheet, export-data,
      and next-batch</li>
  <li><strong>220+ ready-made templates</strong> &mdash; from chemical reactors to
      Kubernetes tuning to bread baking</li>
  <li><strong>Complete statistical analysis</strong> &mdash; ANOVA, main effects,
      interactions, Pareto charts, normal probability plots, model diagnostics,
      response surface modeling, and multi-objective optimization</li>
  <li><strong>Automated and manual workflows</strong> &mdash; generate runner scripts
      or record results by hand</li>
  <li><strong>Interactive HTML reports</strong> &mdash; self-contained reports with
      embedded charts that you can share with your team</li>
</ul>

<p>Everything in this book is based on version 0.1.0 of the <code>doehelper</code>
package, installable via <code>pip install doehelper</code>.</p>
</section>

<!-- ══════════════════════════════════════════
     PART II: USER'S GUIDE
     ══════════════════════════════════════════ -->
<div class="part-title">
  <div class="part-number">Part II</div>
  <h1>User&rsquo;s Guide</h1>
  <div class="part-subtitle">Hands-On Walkthrough of Every Feature</div>
</div>

{guide}

<!-- ══════════════════════════════════════════
     PART III: TECHNICAL REFERENCE
     ══════════════════════════════════════════ -->
<div class="part-title">
  <div class="part-number">Part III</div>
  <h1>Technical Reference</h1>
  <div class="part-subtitle">Complete CLI, Configuration, and Formula Specification</div>
</div>

{reference}

<!-- ══════════════════════════════════════════
     PART IV: DOE THEORY
     ══════════════════════════════════════════ -->
<div class="part-title">
  <div class="part-number">Part IV</div>
  <h1>Design of Experiments</h1>
  <div class="part-subtitle">A Practical Guide &mdash; From Theory to Automated Analysis</div>
</div>

{theory}

</body>
</html>"""


def main():
    print("Building book HTML...")
    html = build_book_html()

    # Write intermediate HTML for inspection
    html_path = OUTPUT.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"  Wrote intermediate HTML: {html_path} ({len(html):,} chars)")

    print("Rendering PDF with WeasyPrint (this may take a minute)...")
    import weasyprint
    doc = weasyprint.HTML(string=html, base_url=str(WEBSITE))
    doc.write_pdf(str(OUTPUT))
    print(f"  Wrote PDF: {OUTPUT}")

    # Report page count
    try:
        from weasyprint import HTML
        pages = HTML(string=html, base_url=str(WEBSITE)).render().pages
        print(f"  Total pages: {len(pages)}")
    except Exception:
        pass

    print("Done!")


if __name__ == "__main__":
    main()
