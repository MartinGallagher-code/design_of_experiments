#!/usr/bin/env bash
# Simulated: Coffee Brewing Extraction
set -euo pipefail

OUTFILE=""
GS=""
WT=""
BT=""
RA=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --grind_size) GS="$2"; shift 2 ;;
        --water_temp) WT="$2"; shift 2 ;;
        --brew_time) BT="$2"; shift 2 ;;
        --ratio) RA="$2"; shift 2 ;;
        --roast_level) shift 2 ;;
        --water_tds) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GS" ] || [ -z "$WT" ] || [ -z "$BT" ] || [ -z "$RA" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GS="$GS" -v WT="$WT" -v BT="$BT" -v RA="$RA" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gs = (GS - 500) / 300;
    wt = (WT - 90.5) / 5.5;
    bt = (BT - 240) / 60;
    ra = (RA - 16) / 2;
    flav = 78 + 3*gs - 2*wt + 4*bt + 2*ra - 3*gs*gs - 2*wt*wt - 2*bt*bt - 1*ra*ra + 1.5*gs*bt + 1*wt*ra;
    bit = 5 - 1.5*gs + 1.2*wt + 0.8*bt - 0.5*ra + 0.6*wt*wt + 0.4*bt*bt + 0.5*wt*bt;
    if (flav < 50) flav = 50; if (flav > 100) flav = 100;
    if (bit < 1) bit = 1; if (bit > 10) bit = 10;
    printf "{\"flavor_score\": %.1f, \"bitterness\": %.1f}", flav + n1*2, bit + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
