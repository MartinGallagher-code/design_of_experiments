#!/usr/bin/env bash
# Simulated: Tire Pressure & Fuel Economy
set -euo pipefail

OUTFILE=""
FP=""
RP=""
LK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --front_psi) FP="$2"; shift 2 ;;
        --rear_psi) RP="$2"; shift 2 ;;
        --load_kg) LK="$2"; shift 2 ;;
        --vehicle) shift 2 ;;
        --tire_model) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$FP" ] || [ -z "$RP" ] || [ -z "$LK" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v FP="$FP" -v RP="$RP" -v LK="$LK" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    fp = (FP - 33) / 5;
    rp = (RP - 33) / 5;
    lk = (LK - 250) / 150;
    mpg = 32 + 1.5*fp + 1.2*rp - 2.5*lk - 0.8*fp*fp - 0.6*rp*rp + 0.4*fp*rp - 0.3*fp*lk;
    wear = 1.8 - 0.3*fp - 0.2*rp + 0.5*lk + 0.2*fp*fp + 0.15*rp*rp + 0.1*fp*lk;
    if (mpg < 15) mpg = 15;
    if (wear < 0.3) wear = 0.3;
    printf "{\"mpg\": %.1f, \"wear_rate\": %.2f}", mpg + n1*0.8, wear + n2*0.1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
