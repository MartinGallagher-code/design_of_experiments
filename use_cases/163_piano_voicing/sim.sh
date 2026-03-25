#!/usr/bin/env bash
# Simulated: Piano Voicing & Regulation
set -euo pipefail

OUTFILE=""
HH=""
LO=""
AT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --hammer_hardness) HH="$2"; shift 2 ;;
        --letoff_mm) LO="$2"; shift 2 ;;
        --aftertouch_mm) AT="$2"; shift 2 ;;
        --piano_type) shift 2 ;;
        --action) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$HH" ] || [ -z "$LO" ] || [ -z "$AT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v HH="$HH" -v LO="$LO" -v AT="$AT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    hh = (HH - 55) / 25;
    lo = (LO - 2.5) / 1.5;
    at = (AT - 1.5) / 1;
    tone = 6.5 - 0.5*hh + 0.3*lo + 0.2*at - 0.8*hh*hh - 0.3*lo*lo + 0.2*hh*lo;
    touch = 6.0 + 0.3*hh - 0.5*lo + 0.8*at - 0.3*hh*hh + 0.2*lo*lo - 0.4*at*at + 0.2*lo*at;
    if (tone < 1) tone = 1; if (tone > 10) tone = 10;
    if (touch < 1) touch = 1; if (touch > 10) touch = 10;
    printf "{\"tonal_evenness\": %.1f, \"touch_response\": %.1f}", tone + n1*0.3, touch + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
