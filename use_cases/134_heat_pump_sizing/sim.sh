#!/usr/bin/env bash
# Simulated: Heat Pump Sizing & Settings
set -euo pipefail

OUTFILE=""
CK=""
BT=""
DI=""
FS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --capacity_kw) CK="$2"; shift 2 ;;
        --backup_threshold_c) BT="$2"; shift 2 ;;
        --defrost_interval) DI="$2"; shift 2 ;;
        --fan_speed) FS="$2"; shift 2 ;;
        --house_sqft) shift 2 ;;
        --climate_zone) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$CK" ] || [ -z "$BT" ] || [ -z "$DI" ] || [ -z "$FS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v CK="$CK" -v BT="$BT" -v DI="$DI" -v FS="$FS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ck = (CK - 8.5) / 3.5;
    bt = (BT - -2.5) / 7.5;
    di = (DI - 60) / 30;
    fs = (FS == "high") ? 1 : -1;
    cost = 900 + 60*ck - 40*bt + 20*di + 30*fs + 15*ck*bt - 10*di*fs;
    comf = 88 + 4*ck + 2*bt - 1*di + 1.5*fs - 1*ck*ck + 0.5*ck*fs;
    if (cost < 400) cost = 400;
    if (comf < 60) comf = 60; if (comf > 100) comf = 100;
    printf "{\"annual_cost\": %.0f, \"comfort_hrs_pct\": %.0f}", cost + n1*25, comf + n2*1.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
