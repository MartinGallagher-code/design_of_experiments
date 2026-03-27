#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated: Engine Oil Change Interval
set -euo pipefail

OUTFILE=""
VW=""
CI=""
FQ=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --viscosity_w) VW="$2"; shift 2 ;;
        --change_interval) CI="$2"; shift 2 ;;
        --filter_quality) FQ="$2"; shift 2 ;;
        --engine_type) shift 2 ;;
        --driving_style) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$VW" ] || [ -z "$CI" ] || [ -z "$FQ" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v VW="$VW" -v CI="$CI" -v FQ="$FQ" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    vw = (VW - 5) / 5;
    ci = (CI - 6500) / 3500;
    fq = (FQ - 3) / 2;
    health = 82 + 3*vw - 8*ci + 5*fq - 1.5*vw*vw - 3*ci*ci - 1*fq*fq + 2*ci*fq;
    cost = 120 + 10*vw - 30*ci + 25*fq + 5*vw*fq;
    if (health < 30) health = 30; if (health > 100) health = 100;
    if (cost < 40) cost = 40;
    printf "{\"engine_health\": %.0f, \"annual_cost\": %.0f}", health + n1*3, cost + n2*8;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
