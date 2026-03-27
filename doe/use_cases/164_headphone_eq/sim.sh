#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Headphone EQ Calibration
set -euo pipefail

OUTFILE=""
BB=""
MP=""
TR=""
SW=""
CF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --bass_boost_db) BB="$2"; shift 2 ;;
        --mid_presence_db) MP="$2"; shift 2 ;;
        --treble_rolloff_db) TR="$2"; shift 2 ;;
        --soundstage_pct) SW="$2"; shift 2 ;;
        --crossfeed_pct) CF="$2"; shift 2 ;;
        --headphone) shift 2 ;;
        --source) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BB" ] || [ -z "$MP" ] || [ -z "$TR" ] || [ -z "$SW" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BB="$BB" -v MP="$MP" -v TR="$TR" -v SW="$SW" -v CF="$CF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bb = (BB - 4) / 4;
    mp = (MP - 0) / 3;
    tr = (TR - -3) / 3;
    sw = (SW - 50) / 50;
    cf = (CF - 30) / 30;
    pref = 6.0 + 0.8*bb + 0.5*mp - 0.3*tr + 0.4*sw + 0.3*cf - 0.5*bb*bb - 0.3*mp*mp;
    fat = 4.0 + 0.5*bb + 0.8*mp + 1.0*tr - 0.3*sw - 0.2*cf + 0.3*mp*tr;
    if (pref < 1) pref = 1; if (pref > 10) pref = 10;
    if (fat < 1) fat = 1; if (fat > 10) fat = 10;
    printf "{\"preference_score\": %.1f, \"fatigue_score\": %.1f}", pref + n1*0.3, fat + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
