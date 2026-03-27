#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Telescope Observation Quality
set -euo pipefail

OUTFILE=""
AP=""
FR=""
EP=""
TR=""
CD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --aperture_mm) AP="$2"; shift 2 ;;
        --focal_ratio) FR="$2"; shift 2 ;;
        --eyepiece_mm) EP="$2"; shift 2 ;;
        --tracking_rate) TR="$2"; shift 2 ;;
        --cooldown_min) CD="$2"; shift 2 ;;
        --mount_type) shift 2 ;;
        --site) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AP" ] || [ -z "$FR" ] || [ -z "$EP" ] || [ -z "$TR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AP="$AP" -v FR="$FR" -v EP="$EP" -v TR="$TR" -v CD="$CD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ap = (AP - 190) / 110;
    fr = (FR - 8) / 4;
    ep = (EP - 15.5) / 9.5;
    tr = (TR - 1.25) / 0.75;
    cd = (CD - 52.5) / 37.5;
    sharp = 6.0 + 0.8*ap + 0.5*fr - 0.3*ep - 1.0*tr + 0.6*cd + 0.2*ap*cd;
    mag = 11 + 1.5*ap + 0.3*fr - 0.2*ep - 0.5*tr + 0.3*cd + 0.2*ap*fr;
    if (sharp < 1) sharp = 1; if (sharp > 10) sharp = 10;
    if (mag < 8) mag = 8;
    printf "{\"sharpness\": %.1f, \"limiting_mag\": %.1f}", sharp + n1*0.3, mag + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
