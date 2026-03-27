#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Landscape Photo Exposure
set -euo pipefail

OUTFILE=""
ISO=""
AP=""
SS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --iso) ISO="$2"; shift 2 ;;
        --aperture) AP="$2"; shift 2 ;;
        --shutter_speed_ms) SS="$2"; shift 2 ;;
        --lens_mm) shift 2 ;;
        --white_balance) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$ISO" ] || [ -z "$AP" ] || [ -z "$SS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v ISO="$ISO" -v AP="$AP" -v SS="$SS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    iso_ = (ISO - 1650) / 1550;
    ap = (AP - 9.4) / 6.6;
    ss = (SS - 500.5) / 499.5;
    dr = 11 - 2*iso_ + 1.5*ap + 0.5*ss - 0.8*iso_*iso_ - 0.5*ap*ap + 0.3*iso_*ap;
    noise = 3 + 3*iso_ - 0.5*ap + 0.2*ss + 1*iso_*iso_ + 0.3*iso_*ss;
    if (dr < 5) dr = 5; if (dr > 15) dr = 15;
    if (noise < 1) noise = 1; if (noise > 10) noise = 10;
    printf "{\"dynamic_range_ev\": %.1f, \"noise_score\": %.1f}", dr + n1*0.3, noise + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
