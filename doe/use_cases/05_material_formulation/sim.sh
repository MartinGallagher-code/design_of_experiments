#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated material testing — continuous interpolation from LHS.
#
# Model (hidden):
#   tensile_strength ~ 40 + 20*(pr-0.55)/0.25 + 15*(fp-17.5)/12.5 - 10*((ct-160)/40)^2 + 8*(ps_code) + noise
#   flexibility ~ 8 - 3*(pr-0.55)/0.25 + 2*(fp-17.5)/12.5 + 1.5*(ct-160)/40 - 2*(ps_code) + noise
#
# ps_code: fine=-1, medium=0, coarse=1

set -euo pipefail

OUTFILE=""
PR="" FP="" CT="" PS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUTFILE="$2"; shift 2 ;;
        --polymer_ratio)  PR="$2";      shift 2 ;;
        --filler_pct)     FP="$2";      shift 2 ;;
        --cure_temp)      CT="$2";      shift 2 ;;
        --particle_size)  PS="$2";      shift 2 ;;
        --cure_time_min|--ambient_humidity) shift 2 ;;
        *)                shift ;;
    esac
done

if [[ -z "$OUTFILE" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

RESULT=$(awk -v pr="$PR" -v fp="$FP" -v ct="$CT" -v ps="$PS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 6;
    n2 = (rand() - 0.5) * 1.5;

    pr_c = (pr - 0.55) / 0.25;
    fp_c = (fp - 17.5) / 12.5;
    ct_c = (ct - 160) / 40;

    if (ps == "fine")        ps_c = -1;
    else if (ps == "medium") ps_c = 0;
    else                     ps_c = 1;

    ts = 40 + 20*pr_c + 15*fp_c - 10*ct_c*ct_c + 8*ps_c + n1;
    if (ts < 5) ts = 5;

    fl = 8 - 3*pr_c + 2*fp_c + 1.5*ct_c - 2*ps_c + n2;
    if (fl < 0.5) fl = 0.5;

    printf "{\"tensile_strength\": %.1f, \"flexibility\": %.2f}", ts, fl;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
