#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: SIEM Alert Correlation
set -euo pipefail

OUTFILE=""
CW=""
ST=""
MEC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --correlation_window_sec) CW="$2"; shift 2 ;;
        --similarity_threshold) ST="$2"; shift 2 ;;
        --min_event_count) MEC="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CW" ] || [ -z "$ST" ] || [ -z "$MEC" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CW="$CW" -v ST="$ST" -v MEC="$MEC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cw = (CW - 315) / 285;
    st = (ST - 0.6) / 0.3;
    mec = (MEC - 6) / 4;
    red = 55 + 15*cw + 12*st + 8*mec - 5*cw*cw - 4*st*st + 3*cw*st + 2*st*mec;
    miss = 3 + 2*cw + 3*st + 4*mec - 1*cw*cw + 1.5*st*st + 2*mec*mec - 1*cw*mec;
    if (red > 95) red = 95; if (red < 10) red = 10;
    if (miss < 0.1) miss = 0.1;
    printf "{\"alert_reduction_pct\": %.1f, \"missed_incident_rate\": %.2f}", red + n1*3, miss + n2*0.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
