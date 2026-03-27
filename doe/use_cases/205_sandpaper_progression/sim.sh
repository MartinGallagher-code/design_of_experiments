#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Sandpaper Grit Progression
set -euo pipefail

OUTFILE=""
SG=""
GS=""
PR=""
PA=""
DE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --start_grit) SG="$2"; shift 2 ;;
        --grit_steps) GS="$2"; shift 2 ;;
        --pressure_kg) PR="$2"; shift 2 ;;
        --passes) PA="$2"; shift 2 ;;
        --dust_extract) DE="$2"; shift 2 ;;
        --wood) shift 2 ;;
        --final_grit) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SG" ] || [ -z "$GS" ] || [ -z "$PR" ] || [ -z "$PA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SG="$SG" -v GS="$GS" -v PR="$PR" -v PA="$PA" -v DE="$DE" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sg = (SG - 90) / 30; gs = (GS - 3.5) / 1.5; pr = (PR - 1.75) / 1.25; pa = (PA - 6.5) / 3.5; de = (DE - 0.5) / 0.5;
    fin = 5.5 - 0.5*sg + 1.0*gs + 0.3*pr + 0.8*pa + 0.2*de + 0.2*gs*pa;
    time_ = 10 + 3*sg + 5*gs + 2*pr + 4*pa - 1*de + 1*gs*pa;
    if (fin < 1) fin = 1; if (fin > 10) fin = 10; if (time_ < 3) time_ = 3;
    printf "{\"finish_score\": %.1f, \"time_min\": %.0f}", fin + n1*0.3, time_ + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
