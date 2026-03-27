#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Podcast Recording Quality
set -euo pipefail

OUTFILE=""
MD=""
GN=""
TR=""
GT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --mic_dist_cm) MD="$2"; shift 2 ;;
        --gain_db) GN="$2"; shift 2 ;;
        --treatment_pct) TR="$2"; shift 2 ;;
        --gate_db) GT="$2"; shift 2 ;;
        --mic_type) shift 2 ;;
        --sample_rate) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$MD" ] || [ -z "$GN" ] || [ -z "$TR" ] || [ -z "$GT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v MD="$MD" -v GN="$GN" -v TR="$TR" -v GT="$GT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    md = (MD - 17.5) / 12.5;
    gn = (GN - 35) / 15;
    tr = (TR - 40) / 40;
    gt = (GT - -45) / 15;
    clarity = 6.5 - 0.8*md + 0.5*gn + 1.0*tr + 0.3*gt - 0.3*md*md - 0.4*gn*gn + 0.2*md*gn;
    noise = -40 + 3*md + 5*gn - 8*tr + 4*gt + 2*gn*gn;
    if (clarity < 1) clarity = 1; if (clarity > 10) clarity = 10;
    if (noise < -70) noise = -70;
    printf "{\"clarity_score\": %.1f, \"noise_floor_db\": %.0f}", clarity + n1*0.3, noise + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
