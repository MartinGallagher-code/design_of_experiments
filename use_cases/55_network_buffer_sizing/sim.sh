#!/usr/bin/env bash
# Simulated: Network Buffer Sizing
set -euo pipefail

OUTFILE=""
NB=""
TQ=""
TW=""
BL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --netdev_budget) NB="$2"; shift 2 ;;
        --txqueuelen) TQ="$2"; shift 2 ;;
        --tcp_wmem_max_kb) TW="$2"; shift 2 ;;
        --backlog_max) BL="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$NB" ] || [ -z "$TQ" ] || [ -z "$TW" ] || [ -z "$BL" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v NB="$NB" -v TQ="$TQ" -v TW="$TW" -v BL="$BL" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    nb = (NB - 576) / 448;
    tq = (TQ - 5250) / 4750;
    tw = (TW - 8320) / 8064;
    bl = (BL - 33268) / 32268;
    thr = 8 + 1.5*nb + 0.5*tq + 2*tw + 0.8*bl - 0.6*nb*nb + 0.3*nb*tw - 0.4*tq*tq;
    sirq = 12 + 5*nb - 1*tq + 2*tw + 3*bl + 1.5*nb*bl - 0.8*nb*nb;
    if (thr < 0.5) thr = 0.5; if (thr > 25) thr = 25;
    if (sirq < 1) sirq = 1;
    printf "{\"throughput_gbps\": %.1f, \"softirq_pct\": %.1f}", thr + n1*0.5, sirq + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
