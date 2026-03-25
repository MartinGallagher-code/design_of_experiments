#!/usr/bin/env bash
# Simulated: Small Wind Turbine Siting
set -euo pipefail

OUTFILE=""
TH=""
RD=""
OD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --tower_height_m) TH="$2"; shift 2 ;;
        --rotor_diam_m) RD="$2"; shift 2 ;;
        --obstacle_dist_m) OD="$2"; shift 2 ;;
        --avg_wind_speed) shift 2 ;;
        --terrain) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$TH" ] || [ -z "$RD" ] || [ -z "$OD" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v TH="$TH" -v RD="$RD" -v OD="$OD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    th = (TH - 20) / 10;
    rd = (RD - 4.5) / 2.5;
    od = (OD - 60) / 40;
    kwh = 3000 + 800*th + 1200*rd + 400*od - 150*th*th - 200*rd*rd + 100*th*rd;
    noise = 42 + 3*th + 5*rd - 6*od + 1*rd*rd + 2*th*rd;
    if (kwh < 500) kwh = 500;
    if (noise < 25) noise = 25;
    printf "{\"annual_kwh\": %.0f, \"noise_dba\": %.0f}", kwh + n1*150, noise + n2*2;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
