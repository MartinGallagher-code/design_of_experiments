#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Natural Deodorant Efficacy
set -euo pipefail

OUTFILE=""
BS=""
AR=""
CO=""
EO=""
BW=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --baking_soda_pct) BS="$2"; shift 2 ;;
        --arrowroot_pct) AR="$2"; shift 2 ;;
        --coconut_oil_pct) CO="$2"; shift 2 ;;
        --eo_drops) EO="$2"; shift 2 ;;
        --beeswax_pct) BW="$2"; shift 2 ;;
        --container) shift 2 ;;
        --batch_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BS" ] || [ -z "$AR" ] || [ -z "$CO" ] || [ -z "$EO" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BS="$BS" -v AR="$AR" -v CO="$CO" -v EO="$EO" -v BW="$BW" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bs = (BS - 15) / 10; ar = (AR - 20) / 10; co = (CO - 35) / 15; eo = (EO - 12.5) / 7.5; bw = (BW - 6) / 4;
    odor = 6 + 3*bs + 1*ar + 0.5*co + 1.5*eo + 0.3*bw + 0.5*bs*eo;
    sens = 3 + 2*bs - 0.5*ar + 0.3*co + 0.8*eo + 0.2*bw + 0.5*bs*bs + 0.3*bs*eo;
    if (odor < 2) odor = 2; if (sens < 1) sens = 1; if (sens > 10) sens = 10;
    printf "{\"odor_control_hrs\": %.0f, \"sensitivity_score\": %.1f}", odor + n1*0.5, sens + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
