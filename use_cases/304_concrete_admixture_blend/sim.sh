#!/usr/bin/env bash
# Simulated concrete admixture blend — produces compressive_strength_28d and workability.
#
# Mixture design: fly_ash + silica_fume + slag = 100%.
# Silica fume boosts strength but hurts workability. Fly ash improves workability.
# Slag provides balanced properties. Synergies exist between components.

set -euo pipefail

OUTFILE=""
FLY_ASH=""
SILICA_FUME=""
SLAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)                OUTFILE="$2";      shift 2 ;;
        --fly_ash)            FLY_ASH="$2";      shift 2 ;;
        --silica_fume)        SILICA_FUME="$2";  shift 2 ;;
        --slag)               SLAG="$2";         shift 2 ;;
        --cement_base)        shift 2 ;;
        --water_cement_ratio) shift 2 ;;
        *)                    shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$FLY_ASH" || -z "$SILICA_FUME" || -z "$SLAG" ]]; then
    echo "Usage: sim.sh --fly_ash FA --silica_fume SF --slag SL --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v fa="$FLY_ASH" -v sf="$SILICA_FUME" -v sl="$SLAG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 3;
    n2 = (rand() - 0.5) * 10;

    # Normalize to fractions (they should sum to 100)
    total = fa + sf + sl;
    if (total < 1) total = 100;
    x1 = fa / total;
    x2 = sf / total;
    x3 = sl / total;

    # Scheffe cubic mixture model for compressive strength (MPa)
    # Pure component contributions
    cs = 35*x1 + 52*x2 + 42*x3;
    # Binary blending synergies
    cs = cs + 12*x1*x2 + 8*x1*x3 + 15*x2*x3;
    # Ternary blending
    cs = cs + 20*x1*x2*x3;
    cs = cs + n1;
    if (cs < 15) cs = 15;
    if (cs > 70) cs = 70;

    # Scheffe model for workability (mm slump)
    wk = 160*x1 + 70*x2 + 120*x3;
    wk = wk - 40*x1*x2 + 30*x1*x3 + 10*x2*x3;
    wk = wk + 50*x1*x2*x3;
    wk = wk + n2;
    if (wk < 30) wk = 30;
    if (wk > 220) wk = 220;

    printf "{\"compressive_strength_28d\": %.1f, \"workability\": %.1f}", cs, wk;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
