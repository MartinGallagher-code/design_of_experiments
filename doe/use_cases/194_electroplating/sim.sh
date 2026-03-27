#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Electroplating Thickness Control
set -euo pipefail

OUTFILE=""
CD=""
BT=""
TM=""
PH=""
AG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --current_density) CD="$2"; shift 2 ;;
        --bath_temp_c) BT="$2"; shift 2 ;;
        --time_min) TM="$2"; shift 2 ;;
        --bath_ph) PH="$2"; shift 2 ;;
        --agitation_rpm) AG="$2"; shift 2 ;;
        --metal) shift 2 ;;
        --substrate) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CD" ] || [ -z "$BT" ] || [ -z "$TM" ] || [ -z "$PH" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CD="$CD" -v BT="$BT" -v TM="$TM" -v PH="$PH" -v AG="$AG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cd = (CD - 5.5) / 4.5; bt = (BT - 37.5) / 17.5; tm = (TM - 32.5) / 27.5; ph = (PH - 3.5) / 1.5; ag = (AG - 100) / 100;
    thick = 15 + 8*cd + 2*bt + 10*tm + 1*ph + 1*ag + 2*cd*tm;
    adh = 3.5 - 0.3*cd + 0.5*bt + 0.2*tm + 0.4*ph + 0.2*ag - 0.3*cd*cd + 0.1*ph*bt;
    if (thick < 1) thick = 1;
    if (adh < 1) adh = 1; if (adh > 5) adh = 5;
    printf "{\"thickness_um\": %.0f, \"adhesion_score\": %.1f}", thick + n1*1, adh + n2*0.15;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
