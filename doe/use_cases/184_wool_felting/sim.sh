#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Wool Felting Process
set -euo pipefail

OUTFILE=""
WT=""
AG=""
SP=""
MP=""
CM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --water_temp_c) WT="$2"; shift 2 ;;
        --agitation_min) AG="$2"; shift 2 ;;
        --soap_ml_L) SP="$2"; shift 2 ;;
        --merino_pct) MP="$2"; shift 2 ;;
        --compressions) CM="$2"; shift 2 ;;
        --technique) shift 2 ;;
        --thickness) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WT" ] || [ -z "$AG" ] || [ -z "$SP" ] || [ -z "$MP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WT="$WT" -v AG="$AG" -v SP="$SP" -v MP="$MP" -v CM="$CM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wt = (WT - 60) / 20; ag = (AG - 17.5) / 12.5; sp = (SP - 5.5) / 4.5; mp = (MP - 75) / 25; cm = (CM - 30) / 20;
    shrink = 20 + 5*wt + 6*ag + 2*sp + 3*mp + 4*cm + 1*wt*ag + 0.5*mp*cm;
    dens = 5.0 + 0.8*wt + 1.0*ag + 0.3*sp + 0.5*mp + 0.8*cm + 0.2*ag*cm;
    if (shrink < 5) shrink = 5; if (shrink > 50) shrink = 50;
    if (dens < 1) dens = 1; if (dens > 10) dens = 10;
    printf "{\"shrinkage_pct\": %.0f, \"density_score\": %.1f}", shrink + n1*2, dens + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
