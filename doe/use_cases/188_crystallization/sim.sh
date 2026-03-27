#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Crystal Growth Optimization
set -euo pipefail

OUTFILE=""
CR=""
SS=""
SD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --cool_rate_c_hr) CR="$2"; shift 2 ;;
        --supersaturation) SS="$2"; shift 2 ;;
        --seed_mm) SD="$2"; shift 2 ;;
        --solvent) shift 2 ;;
        --compound) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CR" ] || [ -z "$SS" ] || [ -z "$SD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CR="$CR" -v SS="$SS" -v SD="$SD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cr = (CR - 2.75) / 2.25; ss = (SS - 1.3) / 0.2; sd = (SD - 1.05) / 0.95;
    size = 5 - 2*cr + 1.5*ss + 1*sd + 0.5*cr*cr - 0.8*ss*ss + 0.3*sd*sd + 0.5*cr*ss;
    pur = 95 + 2*cr - 3*ss + 0.5*sd - 1*cr*cr + 1.5*ss*ss + 0.5*cr*ss;
    if (size < 0.5) size = 0.5;
    if (pur < 80) pur = 80; if (pur > 100) pur = 100;
    printf "{\"crystal_size_mm\": %.1f, \"purity_pct\": %.1f}", size + n1*0.3, pur + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
