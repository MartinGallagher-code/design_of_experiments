#!/usr/bin/env bash
# Simulated: Solar Panel Tilt & Orientation
set -euo pipefail

OUTFILE=""
TI=""
AZ=""
RS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tilt_deg) TI="$2"; shift 2 ;;
        --azimuth_deg) AZ="$2"; shift 2 ;;
        --row_spacing_m) RS="$2"; shift 2 ;;
        --latitude) shift 2 ;;
        --panel_watt) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TI" ] || [ -z "$AZ" ] || [ -z "$RS" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TI="$TI" -v AZ="$AZ" -v RS="$RS" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ti = (TI - 30) / 20;
    az = (AZ - 180) / 30;
    rs = (RS - 2.75) / 1.25;
    kwh = 580 + 30*ti - 15*az + 10*rs - 20*ti*ti - 10*az*az + 5*ti*rs;
    temp = 65 + 3*ti - 2*az - 4*rs + 1.5*ti*ti + 1*az*az;
    if (kwh < 300) kwh = 300;
    if (temp < 40) temp = 40;
    printf "{\"annual_kwh\": %.0f, \"peak_temp_c\": %.0f}", kwh + n1*15, temp + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
