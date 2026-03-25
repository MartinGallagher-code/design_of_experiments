#!/usr/bin/env bash
# Simulated: Study Session Optimization
set -euo pipefail

OUTFILE=""
BM=""
BR=""
AR=""
ND=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --block_min) BM="$2"; shift 2 ;;
        --break_min) BR="$2"; shift 2 ;;
        --active_recall_pct) AR="$2"; shift 2 ;;
        --noise_db) ND="$2"; shift 2 ;;
        --subject) shift 2 ;;
        --total_hours) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$BM" ] || [ -z "$BR" ] || [ -z "$AR" ] || [ -z "$ND" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v BM="$BM" -v BR="$BR" -v AR="$AR" -v ND="$ND" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    bm = (BM - 32.5) / 17.5;
    br = (BR - 9) / 6;
    ar = (AR - 50) / 50;
    nd = (ND - 45) / 20;
    ret = 60 + 3*bm + 2*br + 10*ar - 2*nd - 2*bm*bm - 1*br*br + 1.5*ar*bm - 0.8*nd*nd;
    att = 6.5 - 0.8*bm + 0.6*br + 0.5*ar - 0.7*nd + 0.3*bm*bm + 0.2*bm*br;
    if (ret < 20) ret = 20; if (ret > 100) ret = 100;
    if (att < 1) att = 1; if (att > 10) att = 10;
    printf "{\"retention_pct\": %.0f, \"attention_score\": %.1f}", ret + n1*4, att + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
