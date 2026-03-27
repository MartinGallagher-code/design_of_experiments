#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Knitting Gauge & Tension
set -euo pipefail

OUTFILE=""
NM=""
YW=""
TS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --needle_mm) NM="$2"; shift 2 ;;
        --yarn_weight) YW="$2"; shift 2 ;;
        --tension_setting) TS="$2"; shift 2 ;;
        --fiber) shift 2 ;;
        --stitch_pattern) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$NM" ] || [ -z "$YW" ] || [ -z "$TS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v NM="$NM" -v YW="$YW" -v TS="$TS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    nm = (NM - 4.5) / 1.5; yw = (YW - 3) / 2; ts = (TS - 6) / 3;
    gauge = 22 - 4*nm - 3*yw + 2*ts + 1*nm*nm + 0.5*yw*yw + 0.5*nm*yw;
    drape = 6.0 + 0.8*nm + 0.3*yw - 0.5*ts - 0.3*nm*nm + 0.2*yw*yw + 0.2*nm*ts;
    if (gauge < 8) gauge = 8; if (gauge > 36) gauge = 36;
    if (drape < 1) drape = 1; if (drape > 10) drape = 10;
    printf "{\"gauge_sts_10cm\": %.0f, \"drape_score\": %.1f}", gauge + n1*1, drape + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
