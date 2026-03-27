#!/usr/bin/env bash
# Simulated pharmaceutical tablet compression — produces hardness, dissolution_rate, friability.
#
# Trade-offs: higher compression increases hardness but reduces dissolution and increases friability risk.
# Binder improves hardness but can slow dissolution. Lubricant reduces friction but weakens tablets.

set -euo pipefail

OUTFILE=""
FORCE=""
GRANULE=""
BINDER=""
LUBRICANT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)               OUTFILE="$2";   shift 2 ;;
        --compression_force) FORCE="$2";     shift 2 ;;
        --granule_size)      GRANULE="$2";   shift 2 ;;
        --binder_pct)        BINDER="$2";    shift 2 ;;
        --lubricant_pct)     LUBRICANT="$2"; shift 2 ;;
        --active_ingredient) shift 2 ;;
        *)                   shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$FORCE" || -z "$GRANULE" || -z "$BINDER" || -z "$LUBRICANT" ]]; then
    echo "Usage: sim.sh --compression_force F --granule_size G --binder_pct B --lubricant_pct L --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v cf="$FORCE" -v gs="$GRANULE" -v bp="$BINDER" -v lp="$LUBRICANT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 8;
    n2 = (rand() - 0.5) * 5;
    n3 = (rand() - 0.5) * 0.2;

    # Coded variables
    cf_c = (cf - 12.5) / 7.5;
    gs_c = (gs - 125) / 75;
    bp_c = (bp - 5) / 3;
    lp_c = (lp - 1.25) / 0.75;

    # Hardness (N): increases with compression and binder, decreases with lubricant
    hard = 120 + 35*cf_c + 15*bp_c - 20*lp_c - 10*gs_c;
    hard = hard - 8*cf_c*cf_c + 5*cf_c*bp_c - 6*lp_c*gs_c + n1;
    if (hard < 20) hard = 20;
    if (hard > 250) hard = 250;

    # Dissolution rate (%): better with smaller granules, worse with high compression/binder
    diss = 82 - 12*cf_c - 8*gs_c - 6*bp_c + 3*lp_c;
    diss = diss - 4*cf_c*bp_c + 3*gs_c*gs_c + 2*lp_c*bp_c + n2;
    if (diss < 20) diss = 20;
    if (diss > 100) diss = 100;

    # Friability (%): lower is better; increases with low compression, large granules
    fri = 0.8 - 0.3*cf_c + 0.2*gs_c - 0.15*bp_c + 0.1*lp_c;
    fri = fri + 0.05*cf_c*lp_c + 0.08*gs_c*gs_c + n3;
    if (fri < 0.01) fri = 0.01;
    if (fri > 4) fri = 4;

    printf "{\"hardness\": %.1f, \"dissolution_rate\": %.1f, \"friability\": %.3f}", hard, diss, fri;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
