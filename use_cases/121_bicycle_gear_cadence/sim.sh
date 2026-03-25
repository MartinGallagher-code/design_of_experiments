#!/usr/bin/env bash
# Simulated: Bicycle Gearing & Cadence
set -euo pipefail

OUTFILE=""
GR=""
CD=""
TP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --gear_ratio) GR="$2"; shift 2 ;;
        --cadence_rpm) CD="$2"; shift 2 ;;
        --tire_psi) TP="$2"; shift 2 ;;
        --terrain) shift 2 ;;
        --rider_weight) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GR" ] || [ -z "$CD" ] || [ -z "$TP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GR="$GR" -v CD="$CD" -v TP="$TP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gr = (GR - 3) / 1;
    cd = (CD - 80) / 20;
    tp = (TP - 85) / 25;
    spd = 25 + 2*gr + 1.5*cd + 0.8*tp - 1*gr*gr - 0.8*cd*cd - 0.3*tp*tp + 0.5*gr*cd;
    eff = 5.0 + 1.2*gr + 0.8*cd - 0.2*tp + 0.5*gr*gr + 0.3*cd*cd + 0.4*gr*cd;
    if (spd < 10) spd = 10;
    if (eff < 1) eff = 1; if (eff > 10) eff = 10;
    printf "{\"avg_speed_kph\": %.1f, \"effort_score\": %.1f}", spd + n1*0.8, eff + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
