#!/usr/bin/env bash
# Simulated: TCP Congestion Control
set -euo pipefail

OUTFILE=""
CA=""
IW=""
RM=""
ECN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --congestion_algo) CA="$2"; shift 2 ;;
        --init_cwnd) IW="$2"; shift 2 ;;
        --rmem_max_kb) RM="$2"; shift 2 ;;
        --ecn) ECN="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CA" ] || [ -z "$IW" ] || [ -z "$RM" ] || [ -z "$ECN" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CA="$CA" -v IW="$IW" -v RM="$RM" -v ECN="$ECN" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ca = (CA == "bbr") ? 1 : -1;
    iw = (IW - 25) / 15;
    rm = (RM - 2176) / 1920;
    ecn = (ECN == "on") ? 1 : -1;
    thr = 7.5 + 1.5*ca + 0.8*iw + 1.2*rm + 0.3*ecn + 0.4*ca*rm + 0.2*iw*rm;
    ret = 1.5 - 0.5*ca - 0.3*iw - 0.2*rm - 0.4*ecn + 0.15*ca*ecn + 0.1*iw*ecn;
    if (thr < 0.1) thr = 0.1; if (thr > 10) thr = 10;
    if (ret < 0.01) ret = 0.01;
    printf "{\"throughput_gbps\": %.2f, \"retransmit_pct\": %.3f}", thr + n1*0.3, ret + n2*0.15;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
