#!/usr/bin/env bash
# Simulated: Room Acoustics Treatment
set -euo pipefail

OUTFILE=""
AB=""
DF=""
BT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --absorption_m2) AB="$2"; shift 2 ;;
        --diffuser_m2) DF="$2"; shift 2 ;;
        --bass_traps) BT="$2"; shift 2 ;;
        --room_m3) shift 2 ;;
        --purpose) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$AB" ] || [ -z "$DF" ] || [ -z "$BT" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v AB="$AB" -v DF="$DF" -v BT="$BT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ab = (AB - 12) / 8;
    df = (DF - 7) / 5;
    bt = (BT - 5) / 3;
    rt = 500 - 100*ab - 30*df - 40*bt + 20*ab*ab + 10*df*df + 5*ab*df;
    flut = 5.0 - 1.0*ab - 1.5*df - 0.3*bt + 0.3*ab*ab + 0.5*df*df + 0.2*ab*df;
    if (rt < 100) rt = 100;
    if (flut < 1) flut = 1; if (flut > 10) flut = 10;
    printf "{\"rt60_ms\": %.0f, \"flutter_echo\": %.1f}", rt + n1*15, flut + n2*0.3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
