#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Zigbee Network Formation
set -euo pipefail

OUTFILE=""
SD=""
MC=""
LC=""
RT=""
PR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --scan_duration_exp) SD="$2"; shift 2 ;;
        --max_children) MC="$2"; shift 2 ;;
        --link_cost_threshold) LC="$2"; shift 2 ;;
        --route_table_size) RT="$2"; shift 2 ;;
        --poll_rate_ms) PR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SD" ] || [ -z "$MC" ] || [ -z "$LC" ] || [ -z "$RT" ] || [ -z "$PR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SD="$SD" -v MC="$MC" -v LC="$LC" -v RT="$RT" -v PR="$PR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sd = (SD - 4.5) / 2.5;
    mc = (MC - 12) / 8;
    lc = (LC - 4) / 3;
    rt = (RT - 30) / 20;
    pr = (PR - 1050) / 950;
    jt = 15 + 5*sd - 3*mc + 2*lc - 2*rt + 4*pr + 1.5*sd*sd + 2*sd*pr - 1*mc*rt;
    stab = 88 + 3*sd + 5*mc - 4*lc + 4*rt - 3*pr - 1.5*sd*sd - 2*mc*mc + 1.5*mc*rt;
    if (jt < 1) jt = 1; if (stab > 100) stab = 100; if (stab < 50) stab = 50;
    printf "{\"join_time_sec\": %.1f, \"network_stability_pct\": %.1f}", jt + n1*2, stab + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
