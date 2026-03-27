#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated web app A/B test — reads factors from environment variables.
#
# Model (hidden): conversion depends mainly on font_size and layout,
# with a mild color_scheme effect.
#   base = 3.2
#   font: small -> -0.8, medium -> +0.5, large -> +0.1
#   layout: grid -> +0.6, list -> -0.3
#   color: dark -> +0.2, light -> -0.1
#   noise ~ U(-0.3, 0.3)

set -euo pipefail

OUTFILE=""

# env arg_style: factors arrive as uppercase env vars; --out still passed as arg
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        *)     shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

RESULT=$(awk \
    -v fs="${FONT_SIZE:-medium}" \
    -v cs="${COLOR_SCHEME:-light}" \
    -v lo="${LAYOUT:-grid}" \
    -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise = (rand() - 0.5) * 0.6;
    base = 3.2;

    if (fs == "small")       base += -0.8;
    else if (fs == "medium") base += 0.5;
    else                     base += 0.1;

    if (lo == "grid") base += 0.6;
    else              base -= 0.3;

    if (cs == "dark") base += 0.2;
    else              base -= 0.1;

    val = base + noise;
    if (val < 0) val = 0;
    printf "{\"conversion_rate\": %.2f}", val;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
