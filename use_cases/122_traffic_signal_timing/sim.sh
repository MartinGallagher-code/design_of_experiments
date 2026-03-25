#!/usr/bin/env bash
# Simulated: Traffic Signal Timing
set -euo pipefail

OUTFILE=""
GS=""
CS=""
OP=""
PP=""
LT=""
SD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --green_sec) GS="$2"; shift 2 ;;
        --cycle_sec) CS="$2"; shift 2 ;;
        --offset_pct) OP="$2"; shift 2 ;;
        --ped_phase_sec) PP="$2"; shift 2 ;;
        --left_turn_sec) LT="$2"; shift 2 ;;
        --sensor_delay) SD="$2"; shift 2 ;;
        --intersection_type) shift 2 ;;
        --time_of_day) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GS" ] || [ -z "$CS" ] || [ -z "$OP" ] || [ -z "$PP" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GS="$GS" -v CS="$CS" -v OP="$OP" -v PP="$PP" -v LT="$LT" -v SD="$SD" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gs = (GS - 37.5) / 22.5;
    cs = (CS - 105) / 45;
    op = (OP - 25) / 25;
    pp = (PP - 20) / 10;
    lt = (LT - 10) / 10;
    sd = (SD - 3) / 2;
    thr = 1200 + 150*gs - 100*cs + 80*op - 60*pp - 40*lt - 30*sd + 20*gs*op;
    wait = 45 - 10*gs + 15*cs - 8*op + 5*pp + 4*lt + 3*sd + 3*cs*pp;
    if (thr < 400) thr = 400;
    if (wait < 5) wait = 5;
    printf "{\"throughput_vph\": %.0f, \"avg_wait_sec\": %.0f}", thr + n1*40, wait + n2*3;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
