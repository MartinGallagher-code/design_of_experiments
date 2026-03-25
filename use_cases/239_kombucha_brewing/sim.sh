#!/usr/bin/env bash
# Simulated: Kombucha Brewing Balance
set -euo pipefail

OUTFILE=""
SG=""
FD=""
TG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --sugar_g_L) SG="$2"; shift 2 ;;
        --ferm_days) FD="$2"; shift 2 ;;
        --tea_g_L) TG="$2"; shift 2 ;;
        --tea_type) shift 2 ;;
        --scoby_age) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$SG" ] || [ -z "$FD" ] || [ -z "$TG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v SG="$SG" -v FD="$FD" -v TG="$TG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sg = (SG - 75) / 25; fd = (FD - 13) / 8; tg = (TG - 10) / 5;
    fizz = 6.0 + 0.8*sg + 1.2*fd + 0.3*tg - 0.3*sg*sg - 0.5*fd*fd + 0.2*sg*fd;
    flav = 6.5 + 0.3*sg + 0.8*fd + 0.6*tg - 0.2*sg*sg - 0.4*fd*fd - 0.2*tg*tg + 0.2*fd*tg;
    if (fizz < 1) fizz = 1; if (fizz > 10) fizz = 10;
    if (flav < 1) flav = 1; if (flav > 10) flav = 10;
    printf "{\"fizz_score\": %.1f, \"flavor_complexity\": %.1f}", fizz + n1*0.3, flav + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
