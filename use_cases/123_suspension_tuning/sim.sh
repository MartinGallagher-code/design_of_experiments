#!/usr/bin/env bash
# Simulated: Suspension Comfort Tuning
set -euo pipefail

OUTFILE=""
SR=""
DS=""
AB=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --spring_rate) SR="$2"; shift 2 ;;
        --damper_setting) DS="$2"; shift 2 ;;
        --arb_stiffness) AB="$2"; shift 2 ;;
        --vehicle_weight) shift 2 ;;
        --tire_size) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SR" ] || [ -z "$DS" ] || [ -z "$AB" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v DS="$DS" -v AB="$AB" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 42.5) / 17.5;
    ds = (DS - 5.5) / 4.5;
    ab = (AB - 27.5) / 12.5;
    comf = 6.5 - 1.2*sr - 0.8*ds - 0.4*ab - 0.5*sr*sr - 0.3*ds*ds + 0.3*sr*ds;
    roll = 3.5 - 0.8*sr - 0.5*ds - 0.6*ab + 0.2*sr*sr + 0.15*ds*ds + 0.2*sr*ab;
    if (comf < 1) comf = 1; if (comf > 10) comf = 10;
    if (roll < 0.5) roll = 0.5;
    printf "{\"comfort_score\": %.1f, \"body_roll_deg\": %.1f}", comf + n1*0.3, roll + n2*0.2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
