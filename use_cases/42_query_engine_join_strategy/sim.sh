#!/usr/bin/env bash
# Simulated: Query Engine Join Strategy
set -euo pipefail

OUTFILE=""
JA=""
HT=""
SB=""
BT=""
AE=""
PT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --join_algorithm) JA="$2"; shift 2 ;;
        --hash_table_mb) HT="$2"; shift 2 ;;
        --sort_buffer_mb) SB="$2"; shift 2 ;;
        --broadcast_threshold_mb) BT="$2"; shift 2 ;;
        --adaptive_execution) AE="$2"; shift 2 ;;
        --partitions) PT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$JA" ] || [ -z "$HT" ] || [ -z "$SB" ] || [ -z "$BT" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v JA="$JA" -v HT="$HT" -v SB="$SB" -v BT="$BT" -v AE="$AE" -v PT="$PT" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    ja = (JA == "hash") ? 1 : -1;
    ht = (HT - 2176) / 1920;
    sb = (SB - 288) / 224;
    bt = (BT - 133) / 123;
    ae = (AE == "on") ? 1 : -1;
    pt = (PT - 225) / 175;
    qt = 45 - 8*ja - 5*ht - 3*sb - 4*bt - 6*ae - 2*pt + 3*ja*ht + 2*ae*pt;
    mem = 12 + 4*ja + 5*ht + 2*sb + 3*bt - 2*ae + 1.5*pt + 1*ja*ht;
    if (qt < 5) qt = 5; if (mem < 2) mem = 2;
    printf "{\"query_time_s\": %.1f, \"peak_memory_gb\": %.1f}", qt + n1*3, mem + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
