#!/usr/bin/env bash
# Simulated: Parking Lot Layout Design
set -euo pipefail

OUTFILE=""
SA=""
AW=""
SW=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --stall_angle) SA="$2"; shift 2 ;;
        --aisle_width) AW="$2"; shift 2 ;;
        --stall_width) SW="$2"; shift 2 ;;
        --lot_area_m2) shift 2 ;;
        --handicap_pct) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SA" ] || [ -z "$AW" ] || [ -z "$SW" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SA="$SA" -v AW="$AW" -v SW="$SW" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sa = (SA - 67.5) / 22.5;
    aw = (AW - 6) / 1.5;
    sw = (SW - 2.7) / 0.3;
    cap = 180 + 15*sa - 20*aw - 25*sw - 5*sa*sa + 3*sa*aw;
    walk = 45 + 5*sa + 3*aw + 2*sw - 2*sa*sa + 1.5*aw*sw;
    if (cap < 80) cap = 80;
    if (walk < 15) walk = 15;
    printf "{\"capacity\": %.0f, \"avg_walk_m\": %.0f}", cap + n1*5, walk + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
