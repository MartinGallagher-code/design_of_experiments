#!/usr/bin/env bash
# Simulated: Kubernetes Pod Autoscaling
set -euo pipefail

OUTFILE=""
CPU=""
WIN=""
REP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --target_cpu_pct) CPU="$2"; shift 2 ;;
        --scaleup_window) WIN="$2"; shift 2 ;;
        --max_replicas) REP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CPU" ] || [ -z "$WIN" ] || [ -z "$REP" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CPU="$CPU" -v WIN="$WIN" -v REP="$REP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    cpu = (CPU - 60) / 20;
    win = (WIN - 67.5) / 52.5;
    rep = (REP - 17.5) / 12.5;
    lat = 120 - 25*cpu + 15*win - 20*rep + 8*cpu*cpu + 6*win*win + 3*rep*rep - 5*cpu*win + 4*cpu*rep;
    cost = 4.5 + 1.2*cpu - 0.3*win + 2.5*rep + 0.4*cpu*rep + 0.3*rep*rep;
    if (lat < 10) lat = 10; if (cost < 0.5) cost = 0.5;
    printf "{\"p99_latency_ms\": %.1f, \"hourly_cost\": %.2f}", lat + n1, cost + n2*0.3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
