#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: WiFi Channel & Power
set -euo pipefail

OUTFILE=""
CW=""
TP=""
GI=""
BF=""
SS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --channel_width) CW="$2"; shift 2 ;;
        --tx_power) TP="$2"; shift 2 ;;
        --guard_interval) GI="$2"; shift 2 ;;
        --beamforming) BF="$2"; shift 2 ;;
        --spatial_streams) SS="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CW" ] || [ -z "$TP" ] || [ -z "$GI" ] || [ -z "$BF" ] || [ -z "$SS" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CW="$CW" -v TP="$TP" -v GI="$GI" -v BF="$BF" -v SS="$SS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cw = (CW - 50) / 30;
    tp = (TP - 16.5) / 6.5;
    gi = (GI == "short") ? 1 : -1;
    bf = (BF == "on") ? 1 : -1;
    ss = (SS - 2.5) / 1.5;
    thr = 500 + 200*cw + 50*tp + 40*gi + 60*bf + 150*ss + 30*cw*ss - 20*cw*cw;
    cov = 25 - 5*cw + 8*tp - 1*gi + 4*bf + 2*ss + 1.5*tp*bf - 2*cw*tp;
    if (thr < 10) thr = 10; if (cov < 5) cov = 5;
    printf "{\"throughput_mbps\": %.0f, \"coverage_m\": %.0f}", thr + n1*30, cov + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
