#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Enzyme Kinetics Assay
set -euo pipefail

OUTFILE=""
SB=""
EN=""
PH=""
TP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --substrate_mm) SB="$2"; shift 2 ;;
        --enzyme_ug) EN="$2"; shift 2 ;;
        --ph) PH="$2"; shift 2 ;;
        --temp_c) TP="$2"; shift 2 ;;
        --enzyme) shift 2 ;;
        --buffer) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SB" ] || [ -z "$EN" ] || [ -z "$PH" ] || [ -z "$TP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SB="$SB" -v EN="$EN" -v PH="$PH" -v TP="$TP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sb = (SB - 5.05) / 4.95; en = (EN - 10.5) / 9.5; ph = (PH - 7) / 2; tp = (TP - 32.5) / 12.5;
    rate = 5 + 2*sb + 3*en + 0.5*ph + 1.5*tp - 1.5*sb*sb - 0.5*en*en - 1*ph*ph - 0.8*tp*tp + 0.5*en*tp;
    inh = 5 + 8*sb - 1*en + 1*ph + 0.5*tp + 5*sb*sb + 1*ph*ph;
    if (rate < 0.1) rate = 0.1;
    if (inh < 0) inh = 0; if (inh > 50) inh = 50;
    printf "{\"reaction_rate\": %.1f, \"inhibition_pct\": %.0f}", rate + n1*0.3, inh + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
