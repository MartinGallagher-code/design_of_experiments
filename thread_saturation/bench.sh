#!/usr/bin/env bash
# Simulated thread saturation benchmark.
# Produces a realistic saturation curve: throughput climbs steeply at
# low thread counts, then flattens.  CPU utilization tracks similarly.
# Latency rises once threads exceed the saturation point.
#
# Usage: ./bench.sh --thread_count N --workload W --matrix_size S --duration_sec D --out path.json

set -euo pipefail

# Parse arguments
OUT=""
THREADS=1
while [[ $# -gt 0 ]]; do
    case "$1" in
        --thread_count) THREADS="$2"; shift 2 ;;
        --out)          OUT="$2";     shift 2 ;;
        *)              shift 2 ;;   # skip other fixed factors
    esac
done

if [[ -z "$OUT" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

# Simulated saturation model (Amdahl-ish):
#   throughput  = base * T / (1 + T/sat)          — saturates around sat
#   cpu_util    = min(100, 15 * T)                 — linear then capped
#   p99_latency = base_lat * (1 + max(0, T-sat)/sat)  — rises past saturation
#
# Add small random noise via $RANDOM.

SAT=8          # saturation knee ~ 8 threads
BASE=50        # base throughput per thread
BASE_LAT=5     # base latency in ms

# bash integer arithmetic + awk for floats
THROUGHPUT=$(awk -v t="$THREADS" -v b="$BASE" -v s="$SAT" \
    'BEGIN { noise = (rand()-0.5)*2; printf "%.2f", b * t / (1 + t/s) + noise }')

CPU=$(awk -v t="$THREADS" \
    'BEGIN { v = 15 * t; if (v > 99) v = 99; noise = (rand()-0.5)*1.5; printf "%.1f", v + noise }')

LATENCY=$(awk -v t="$THREADS" -v bl="$BASE_LAT" -v s="$SAT" \
    'BEGIN { extra = (t > s) ? (t - s)/s : 0; noise = (rand()-0.5)*0.8; printf "%.2f", bl * (1 + extra) + noise }')

mkdir -p "$(dirname "$OUT")"
cat > "$OUT" <<EOF
{
  "throughput": $THROUGHPUT,
  "cpu_util": $CPU,
  "p99_latency": $LATENCY
}
EOF

echo "  -> throughput=$THROUGHPUT ops/s, cpu=$CPU%, p99=${LATENCY}ms"
