#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: BGP Route Convergence
set -euo pipefail

OUTFILE=""
KA=""
HT=""
MR=""
DMP=""
BFD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --keepalive_s) KA="$2"; shift 2 ;;
        --hold_time_s) HT="$2"; shift 2 ;;
        --mrai_s) MR="$2"; shift 2 ;;
        --dampening) DMP="$2"; shift 2 ;;
        --bfd) BFD="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$KA" ] || [ -z "$HT" ] || [ -z "$MR" ] || [ -z "$DMP" ] || [ -z "$BFD" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v KA="$KA" -v HT="$HT" -v MR="$MR" -v DMP="$DMP" -v BFD="$BFD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ka = (KA - 35) / 25;
    ht = (HT - 105) / 75;
    mr = (MR - 17.5) / 12.5;
    dmp = (DMP == "on") ? 1 : -1;
    bfd = (BFD == "on") ? 1 : -1;
    conv = 45 + 12*ka + 15*ht + 8*mr + 5*dmp - 20*bfd + 3*ka*ht - 4*bfd*ka;
    stab = 85 - 3*ka - 5*ht - 2*mr + 8*dmp + 3*bfd - 2*ka*ht + 3*dmp*bfd;
    if (conv < 1) conv = 1; if (stab > 100) stab = 100; if (stab < 50) stab = 50;
    printf "{\"convergence_time_s\": %.1f, \"route_stability\": %.1f}", conv + n1*4, stab + n2*2;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
