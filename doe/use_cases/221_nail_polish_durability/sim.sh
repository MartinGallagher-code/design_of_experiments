#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Nail Polish Durability
set -euo pipefail

OUTFILE=""
BC=""
CC=""
TT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --base_coats) BC="$2"; shift 2 ;;
        --color_coats) CC="$2"; shift 2 ;;
        --topcoat_thickness) TT="$2"; shift 2 ;;
        --prep) shift 2 ;;
        --cure) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BC" ] || [ -z "$CC" ] || [ -z "$TT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BC="$BC" -v CC="$CC" -v TT="$TT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bc = (BC - 1.5) / 0.5; cc = (CC - 2) / 1; tt = (TT - 2) / 1;
    days = 5 + 1.5*bc + 1*cc + 2*tt - 0.5*bc*bc - 0.3*cc*cc + 0.3*bc*tt;
    gloss = 75 + 5*bc + 3*cc + 8*tt - 2*bc*bc - 1*cc*cc - 3*tt*tt + 1*cc*tt;
    if (days < 1) days = 1; if (gloss < 40) gloss = 40; if (gloss > 100) gloss = 100;
    printf "{\"days_no_chip\": %.0f, \"gloss_retention_pct\": %.0f}", days + n1*0.5, gloss + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
