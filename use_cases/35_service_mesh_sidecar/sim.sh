#!/usr/bin/env bash
# Simulated: Service Mesh Sidecar
set -euo pipefail

OUTFILE=""
CON=""
CB=""
AL=""
TR=""
COMP=""
CP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --concurrency) CON="$2"; shift 2 ;;
        --circuit_breaker_max) CB="$2"; shift 2 ;;
        --access_log) AL="$2"; shift 2 ;;
        --tracing_sample_pct) TR="$2"; shift 2 ;;
        --compression) COMP="$2"; shift 2 ;;
        --connection_pool) CP="$2"; shift 2 ;;
        *) shift ;;
    esac
done

if [[ -z "$OUTFILE" ]] || [ -z "$CON" ] || [ -z "$CB" ] || [ -z "$AL" ] || [ -z "$TR" ]; then
    echo "ERROR: missing required arguments" >&2
    exit 1
fi

RESULT=$(awk -v CON="$CON" -v CB="$CB" -v AL="$AL" -v TR="$TR" -v COMP="$COMP" -v CP="$CP" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    con = (CON - 4.5) / 3.5;
    cb = (CB - 5050) / 4950;
    al = (AL == "on") ? 1 : -1;
    tr = (TR - 50.5) / 49.5;
    comp = (COMP == "on") ? 1 : -1;
    cp = (CP - 550) / 450;
    lat = 3.0 - 1.2*con + 0.3*cb + 0.8*al + 1.5*tr + 0.6*comp - 0.4*cp + 0.3*al*tr;
    cpu = 8 + 5*con + 1*cb + 3*al + 4*tr + 2*comp + 1.5*cp + 1*con*tr;
    if (lat < 0.2) lat = 0.2; if (cpu < 1) cpu = 1;
    printf "{\"latency_overhead_ms\": %.1f, \"sidecar_cpu_pct\": %.1f}", lat + n1*0.3, cpu + n2*1.5;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
