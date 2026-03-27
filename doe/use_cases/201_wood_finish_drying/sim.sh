#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Wood Finish Drying Conditions
set -euo pipefail

OUTFILE=""
TP=""
HM=""
AF=""
CM=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --humidity_pct) HM="$2"; shift 2 ;;
        --air_flow) AF="$2"; shift 2 ;;
        --coat_mils) CM="$2"; shift 2 ;;
        --finish_type) shift 2 ;;
        --wood) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TP" ] || [ -z "$HM" ] || [ -z "$AF" ] || [ -z "$CM" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TP="$TP" -v HM="$HM" -v AF="$AF" -v CM="$CM" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    tp = (TP - 22.5) / 7.5; hm = (HM - 50) / 20; af = (AF == "on") ? 1 : -1; cm = (CM - 4) / 2;
    dry = 4.0 - 1.2*tp + 0.8*hm - 0.6*af + 1.0*cm + 0.3*tp*tp + 0.2*hm*cm;
    hard = 6.0 + 0.5*tp - 0.3*hm + 0.2*af - 0.4*cm - 0.2*tp*tp + 0.1*af*cm;
    if (dry < 0.5) dry = 0.5; if (hard < 1) hard = 1; if (hard > 10) hard = 10;
    printf "{\"dry_time_hrs\": %.1f, \"hardness_h\": %.1f}", dry + n1*0.3, hard + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
