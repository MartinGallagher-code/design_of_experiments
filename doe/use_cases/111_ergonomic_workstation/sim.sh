#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Ergonomic Workstation Setup
set -euo pipefail

OUTFILE=""
DH=""
MD=""
CR=""
BF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --desk_height_cm) DH="$2"; shift 2 ;;
        --monitor_dist_cm) MD="$2"; shift 2 ;;
        --chair_recline_deg) CR="$2"; shift 2 ;;
        --break_freq_min) BF="$2"; shift 2 ;;
        --monitor_size) shift 2 ;;
        --chair_type) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DH" ] || [ -z "$MD" ] || [ -z "$CR" ] || [ -z "$BF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DH="$DH" -v MD="$MD" -v CR="$CR" -v BF="$BF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dh = (DH - 72.5) / 7.5;
    md = (MD - 65) / 15;
    cr = (CR - 102.5) / 12.5;
    bf = (BF - 57.5) / 32.5;
    comf = 6.0 + 0.3*dh + 0.5*md + 0.8*cr - 0.6*bf - 0.8*dh*dh - 0.4*md*md - 0.3*cr*cr + 0.3*cr*bf;
    prod = 95 + 1*dh + 1.5*md + 0.5*cr - 2*bf - 1.5*dh*dh - 1*md*md + 0.5*md*bf;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    if (prod < 70) prod = 70; if (prod > 115) prod = 115;
    printf "{\"comfort_score\": %.1f, \"productivity_pct\": %.0f}", comf + n1*0.3, prod + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
