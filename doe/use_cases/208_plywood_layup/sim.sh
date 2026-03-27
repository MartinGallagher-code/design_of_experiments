#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Plywood Layup Optimization
set -euo pipefail

OUTFILE=""
VN=""
GW=""
PT=""
PM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --veneer_mm) VN="$2"; shift 2 ;;
        --glue_g_m2) GW="$2"; shift 2 ;;
        --press_temp_c) PT="$2"; shift 2 ;;
        --press_min) PM="$2"; shift 2 ;;
        --species) shift 2 ;;
        --layers) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$VN" ] || [ -z "$GW" ] || [ -z "$PT" ] || [ -z "$PM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v VN="$VN" -v GW="$GW" -v PT="$PT" -v PM="$PM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    vn = (VN - 2) / 1; gw = (GW - 170) / 50; pt = (PT - 125) / 25; pm = (PM - 6.5) / 3.5;
    bend = 60 - 5*vn + 3*gw + 4*pt + 2*pm + 1*vn*vn + 0.5*gw*pt;
    delam = 4.0 + 0.5*vn - 0.8*gw - 0.6*pt - 1.0*pm + 0.3*vn*vn + 0.2*gw*gw + 0.2*vn*pm;
    if (bend < 20) bend = 20; if (delam < 1) delam = 1; if (delam > 10) delam = 10;
    printf "{\"bend_strength_mpa\": %.0f, \"delam_score\": %.1f}", bend + n1*3, delam + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
