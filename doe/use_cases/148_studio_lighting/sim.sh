#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Studio Portrait Lighting
set -euo pipefail

OUTFILE=""
KP=""
FR=""
MC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --key_power_ws) KP="$2"; shift 2 ;;
        --fill_ratio) FR="$2"; shift 2 ;;
        --modifier_cm) MC="$2"; shift 2 ;;
        --background) shift 2 ;;
        --distance_m) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$KP" ] || [ -z "$FR" ] || [ -z "$MC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v KP="$KP" -v FR="$FR" -v MC="$MC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    kp = (KP - 300) / 200;
    fr = (FR - 5) / 3;
    mc = (MC - 105) / 45;
    skin = 7.0 + 0.5*kp - 0.8*fr + 0.6*mc - 0.6*kp*kp - 0.3*fr*fr + 0.2*kp*mc;
    shadow = 5.0 + 0.5*kp + 1.2*fr - 1.5*mc + 0.3*kp*kp + 0.2*fr*fr + 0.3*kp*fr;
    if (skin < 1) skin = 1; if (skin > 10) skin = 10;
    if (shadow < 1) shadow = 1; if (shadow > 10) shadow = 10;
    printf "{\"skin_accuracy\": %.1f, \"shadow_harshness\": %.1f}", skin + n1*0.3, shadow + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
