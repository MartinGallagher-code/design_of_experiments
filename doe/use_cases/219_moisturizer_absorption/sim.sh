#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Moisturizer Absorption Rate
set -euo pipefail

OUTFILE=""
HA=""
EM=""
AM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --ha_pct) HA="$2"; shift 2 ;;
        --emulsifier_pct) EM="$2"; shift 2 ;;
        --amount_mg_cm2) AM="$2"; shift 2 ;;
        --base) shift 2 ;;
        --ph) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HA" ] || [ -z "$EM" ] || [ -z "$AM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HA="$HA" -v EM="$EM" -v AM="$AM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ha = (HA - 1.75) / 1.25; em = (EM - 5) / 3; am = (AM - 2.5) / 1.5;
    hyd = 6.0 + 1.2*ha + 0.5*em + 0.8*am - 0.5*ha*ha - 0.3*em*em + 0.2*ha*am;
    grs = 3.5 + 0.3*ha + 0.8*em + 1.0*am + 0.2*em*em + 0.3*am*am + 0.2*em*am;
    if (hyd < 1) hyd = 1; if (hyd > 10) hyd = 10;
    if (grs < 1) grs = 1; if (grs > 10) grs = 10;
    printf "{\"hydration_depth\": %.1f, \"greasiness\": %.1f}", hyd + n1*0.3, grs + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
