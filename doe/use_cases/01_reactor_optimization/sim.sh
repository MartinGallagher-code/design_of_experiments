#!/usr/bin/env bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Simulated chemical reactor — produces yield, purity, and cost responses.
#
# The underlying model (hidden from the experimenter):
#   yield  = 70 + 8*(T-175)/25 + 5*(P-4)/2 + 3*(C-1.25)/0.75 - 4*(T-175)^2/625 - 2*(P-4)^2/4 + noise
#   purity = 90 + 3*(T-175)/25 - 2*(P-4)/2 + 6*(C-1.25)/0.75 - 1.5*(T-175)^2/625 + noise
#   cost   = 50 + 12*(T-175)/25 + 8*(P-4)/2 + 4*(C-1.25)/0.75 + 2*(T-175)*(P-4)/50 + noise
#
# This gives interesting trade-offs: higher T increases yield but also cost,
# higher catalyst improves purity but adds cost, etc.

set -euo pipefail

OUTFILE=""
TEMP=""
PRESS=""
CATAL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)             OUTFILE="$2"; shift 2 ;;
        --temperature)     TEMP="$2";    shift 2 ;;
        --pressure)        PRESS="$2";   shift 2 ;;
        --catalyst)        CATAL="$2";   shift 2 ;;
        --reaction_time)   shift 2 ;;
        --stirring_speed)  shift 2 ;;
        *)                 shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$TEMP" || -z "$PRESS" || -z "$CATAL" ]]; then
    echo "Usage: reactor_sim.sh --temperature T --pressure P --catalyst C --out FILE" >&2
    exit 1
fi

# Compute responses using awk for floating-point math
RESULT=$(awk -v T="$TEMP" -v P="$PRESS" -v C="$CATAL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 4;
    noise2 = (rand() - 0.5) * 3;
    noise3 = (rand() - 0.5) * 5;

    # Coded variables (centered and scaled)
    t = (T - 175) / 25;
    p = (P - 4) / 2;
    c = (C - 1.25) / 0.75;

    # Yield model: quadratic with interaction
    yield_val = 70 + 8*t + 5*p + 3*c - 4*t*t - 2*p*p + 1.5*t*p + noise1;
    if (yield_val < 0) yield_val = 0;
    if (yield_val > 100) yield_val = 100;

    # Purity model: mostly linear with slight curvature
    purity_val = 90 + 3*t - 2*p + 6*c - 1.5*t*t + noise2;
    if (purity_val < 0) purity_val = 0;
    if (purity_val > 100) purity_val = 100;

    # Cost model: linear with interaction
    cost_val = 50 + 12*t + 8*p + 4*c + 2*t*p + noise3;
    if (cost_val < 0) cost_val = 0;

    printf "{\"yield\": %.2f, \"purity\": %.2f, \"cost\": %.2f}", yield_val, purity_val, cost_val;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
