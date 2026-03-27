#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Wood Stain & Finish
set -euo pipefail

OUTFILE=""
SD=""
NC=""
DH=""
TC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --stain_dilution) SD="$2"; shift 2 ;;
        --num_coats) NC="$2"; shift 2 ;;
        --dry_hrs) DH="$2"; shift 2 ;;
        --topcoat_coats) TC="$2"; shift 2 ;;
        --wood_type) shift 2 ;;
        --stain_color) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SD" ] || [ -z "$NC" ] || [ -z "$DH" ] || [ -z "$TC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SD="$SD" -v NC="$NC" -v DH="$DH" -v TC="$TC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sd = (SD - 25) / 25;
    nc = (NC - 2) / 1;
    dh = (DH - 13) / 11;
    tc = (TC - 2) / 1;
    color = 6.0 - 1.5*sd + 1.2*nc + 0.3*dh + 0.2*tc + 0.4*sd*sd - 0.3*nc*nc + 0.2*nc*dh;
    dur = 5.0 + 0.2*sd + 0.3*nc + 0.4*dh + 2.0*tc - 0.3*tc*tc + 0.2*nc*tc;
    if (color < 1) color = 1; if (color > 10) color = 10;
    if (dur < 1) dur = 1; if (dur > 10) dur = 10;
    printf "{\"color_depth\": %.1f, \"durability\": %.1f}", color + n1*0.4, dur + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
