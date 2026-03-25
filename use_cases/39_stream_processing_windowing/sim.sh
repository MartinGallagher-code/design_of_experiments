#!/usr/bin/env bash
# Simulated: Stream Processing Windowing
set -euo pipefail

OUTFILE=""
WS=""
WD=""
PAR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --window_size_s) WS="$2"; shift 2 ;;
        --watermark_delay_s) WD="$2"; shift 2 ;;
        --parallelism) PAR="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$WS" ] || [ -z "$WD" ] || [ -z "$PAR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v WS="$WS" -v WD="$WD" -v PAR="$PAR" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ws = (WS - 62.5) / 57.5;
    wd = (WD - 15.5) / 14.5;
    par = (PAR - 18) / 14;
    lat = 500 + 300*ws + 200*wd - 150*par + 50*ws*ws + 30*wd*wd + 80*ws*wd - 40*par*ws;
    acc = 92 + 3*ws + 5*wd - 0.5*par - 1.5*ws*ws - 2*wd*wd + 0.8*ws*wd;
    if (lat < 20) lat = 20; if (acc > 100) acc = 100; if (acc < 70) acc = 70;
    printf "{\"end_to_end_latency_ms\": %.0f, \"result_accuracy\": %.1f}", lat + n1*30, acc + n2*1.0;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
