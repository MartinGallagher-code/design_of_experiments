#!/usr/bin/env bash
# Simulated: TLS Handshake Optimization
set -euo pipefail

OUTFILE=""
SC=""
ST=""
OW=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --session_cache_size) SC="$2"; shift 2 ;;
        --session_timeout_s) ST="$2"; shift 2 ;;
        --ocsp_stapling_workers) OW="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$SC" ] || [ -z "$ST" ] || [ -z "$OW" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v SC="$SC" -v ST="$ST" -v OW="$OW" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    sc = (SC - 50500) / 49500;
    st = (ST - 43230) / 43170;
    ow = (OW - 4.5) / 3.5;
    hs = 45 - 12*sc - 8*st - 5*ow + 4*sc*sc + 3*st*st + 1*ow*ow + 2*sc*st;
    res = 55 + 20*sc + 15*st + 3*ow - 5*sc*sc - 4*st*st + 3*sc*st;
    if (hs < 2) hs = 2; if (res > 99) res = 99; if (res < 10) res = 10;
    printf "{\"handshake_ms\": %.1f, \"resumption_rate\": %.1f}", hs + n1*3, res + n2*3;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
