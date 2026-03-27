#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Tomato Greenhouse Yield
set -euo pipefail

OUTFILE=""
DT=""
HM=""
IR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --day_temp) DT="$2"; shift 2 ;;
        --humidity_pct) HM="$2"; shift 2 ;;
        --irrigation_freq) IR="$2"; shift 2 ;;
        --variety) shift 2 ;;
        --light_hours) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$DT" ] || [ -z "$HM" ] || [ -z "$IR" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v DT="$DT" -v HM="$HM" -v IR="$IR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    dt = (DT - 27) / 5;
    hm = (HM - 67.5) / 17.5;
    ir = (IR - 4) / 2;
    yld = 4.5 + 0.8*dt + 0.3*hm + 0.6*ir - 0.5*dt*dt - 0.2*hm*hm - 0.3*ir*ir + 0.2*dt*ir;
    ber = 8 + 3*dt - 2*hm - 1.5*ir + 1.5*dt*dt + 0.5*hm*hm + 1*dt*hm;
    if (yld < 0.5) yld = 0.5;
    if (ber < 0) ber = 0; if (ber > 40) ber = 40;
    printf "{\"yield_kg\": %.2f, \"ber_pct\": %.1f}", yld + n1*0.3, ber + n2*1.0;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
