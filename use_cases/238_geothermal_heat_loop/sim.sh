#!/usr/bin/env bash
# Simulated: Geothermal Ground Loop Design
set -euo pipefail

OUTFILE=""
LD=""
PD=""
FL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --loop_depth_m) LD="$2"; shift 2 ;;
        --pipe_diam_mm) PD="$2"; shift 2 ;;
        --flow_lpm) FL="$2"; shift 2 ;;
        --soil_conductivity) shift 2 ;;
        --grout) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$LD" ] || [ -z "$PD" ] || [ -z "$FL" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v LD="$LD" -v PD="$PD" -v FL="$FL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ld = (LD - 65) / 35; pd = (PD - 32.5) / 7.5; fl = (FL - 10) / 5;
    heat = 6 + 3*ld + 1*pd + 1.5*fl - 0.8*ld*ld - 0.5*pd*pd - 0.5*fl*fl + 0.3*ld*fl;
    cost = 8000 + 3000*ld + 500*pd + 200*fl + 500*ld*ld;
    if (heat < 2) heat = 2; if (cost < 4000) cost = 4000;
    printf "{\"heat_kw\": %.1f, \"install_cost\": %.0f}", heat + n1*0.3, cost + n2*200;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
