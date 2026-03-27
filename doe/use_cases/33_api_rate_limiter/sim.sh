#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: API Rate Limiter Tuning
set -euo pipefail

OUTFILE=""
RPS=""
BS=""
WT=""
PD=""
GL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --requests_per_sec) RPS="$2"; shift 2 ;;
        --burst_size) BS="$2"; shift 2 ;;
        --window_type) WT="$2"; shift 2 ;;
        --penalty_duration) PD="$2"; shift 2 ;;
        --global_limit) GL="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$RPS" ] || [ -z "$BS" ] || [ -z "$WT" ] || [ -z "$PD" ] || [ -z "$GL" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v RPS="$RPS" -v BS="$BS" -v WT="$WT" -v PD="$PD" -v GL="$GL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rps = (RPS - 550) / 450;
    bs = (BS - 55) / 45;
    wt = (WT == "sliding") ? 1 : -1;
    pd = (PD - 155) / 145;
    gl = (GL - 27500) / 22500;
    gp = 8500 + 2000*rps + 800*bs + 500*wt - 600*pd + 3000*gl - 400*rps*pd + 300*bs*gl;
    fair = 0.85 + 0.06*wt - 0.04*rps + 0.03*bs - 0.08*pd + 0.02*gl + 0.02*wt*pd;
    if (gp < 100) gp = 100; if (fair > 1) fair = 1; if (fair < 0.3) fair = 0.3;
    printf "{\"goodput_rps\": %.0f, \"fairness_index\": %.3f}", gp + n1*300, fair + n2*0.02;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
