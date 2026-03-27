#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Photo Print Color Accuracy
set -euo pipefail

OUTFILE=""
PG=""
ID=""
PB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --profile_gamma) PG="$2"; shift 2 ;;
        --ink_density_pct) ID="$2"; shift 2 ;;
        --paper_brightness) PB="$2"; shift 2 ;;
        --printer) shift 2 ;;
        --resolution_dpi) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$PG" ] || [ -z "$ID" ] || [ -z "$PB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v PG="$PG" -v ID="$ID" -v PB="$PB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    pg = (PG - 2.1) / 0.3;
    id = (ID - 100) / 20;
    pb = (PB - 95) / 5;
    de = 5.0 + 1.2*pg + 0.5*id - 0.8*pb + 0.8*pg*pg + 0.3*id*id + 0.2*pg*id;
    ink = 8.0 + 0.3*pg + 2.5*id + 0.1*pb + 0.5*id*id;
    if (de < 0.5) de = 0.5;
    if (ink < 3) ink = 3;
    printf "{\"delta_e\": %.1f, \"ink_ml\": %.1f}", de + n1*0.3, ink + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
