#!/usr/bin/env bash
# Simulated: Rowing Ergometer Performance
set -euo pipefail

OUTFILE=""
SR=""
DR=""
DF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --stroke_rate) SR="$2"; shift 2 ;;
        --drive_ratio) DR="$2"; shift 2 ;;
        --drag_factor) DF="$2"; shift 2 ;;
        --athlete) shift 2 ;;
        --piece) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SR" ] || [ -z "$DR" ] || [ -z "$DF" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SR="$SR" -v DR="$DR" -v DF="$DF" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sr = (SR - 28) / 6; dr = (DR - 2.25) / 0.75; df = (DF - 120) / 20;
    watts = 220 + 20*sr + 10*dr + 8*df - 8*sr*sr - 5*dr*dr - 3*df*df + 3*sr*dr;
    sp = 115 - 5*sr - 3*dr - 2*df + 2*sr*sr + 1*dr*dr + 0.5*df*df - 0.8*sr*dr;
    if (watts < 100) watts = 100; if (sp < 85) sp = 85;
    printf "{\"avg_watts\": %.0f, \"split_500m_sec\": %.0f}", watts + n1*5, sp + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
