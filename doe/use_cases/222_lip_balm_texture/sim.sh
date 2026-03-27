#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Lip Balm Texture Formulation
set -euo pipefail

OUTFILE=""
BW=""
SH=""
OT=""
FL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --beeswax_pct) BW="$2"; shift 2 ;;
        --shea_pct) SH="$2"; shift 2 ;;
        --oil_type) OT="$2"; shift 2 ;;
        --flavor_pct) FL="$2"; shift 2 ;;
        --vitamin_e) shift 2 ;;
        --container) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BW" ] || [ -z "$SH" ] || [ -z "$OT" ] || [ -z "$FL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BW="$BW" -v SH="$SH" -v OT="$OT" -v FL="$FL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bw = (BW - 22.5) / 7.5; sh = (SH - 20) / 10; ot = (OT == "jojoba") ? 1 : -1; fl = (FL - 1.75) / 1.25;
    moist = 6.0 - 0.5*bw + 1.0*sh + 0.3*ot + 0.2*fl + 0.2*bw*sh + 0.1*sh*ot;
    firm = 5.5 + 1.5*bw - 0.5*sh + 0.2*ot - 0.1*fl - 0.3*bw*bw + 0.1*bw*sh;
    if (moist < 1) moist = 1; if (moist > 10) moist = 10;
    if (firm < 1) firm = 1; if (firm > 10) firm = 10;
    printf "{\"moisture_score\": %.1f, \"firmness_score\": %.1f}", moist + n1*0.3, firm + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
