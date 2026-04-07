#!/usr/bin/env bash
# NUMA cross-node memory benchmark runner.
#
# Called by the DOE harness with double-dash arguments:
#   ./bench.sh --buffer_size 67108864 --cpu_id 0 --mem_node 1 \
#              --mode bandwidth_read --out results/run_1.json
#
# --cpu_id pins to an exact logical CPU (physcpubind), so you can
# measure per-core differences within a NUMA node.
#
# Requires: numactl, gcc (for first-run compile)
# The C benchmark (bench.c) is compiled automatically on first use.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BIN="$SCRIPT_DIR/bench"
BENCH_SRC="$SCRIPT_DIR/bench.c"

# ── Compile if needed ───────────────────────────────────────────────
if [[ ! -x "$BENCH_BIN" ]] || [[ "$BENCH_SRC" -nt "$BENCH_BIN" ]]; then
    echo "Compiling $BENCH_SRC ..." >&2
    gcc -O2 -o "$BENCH_BIN" "$BENCH_SRC" -lm
fi

# ── Parse arguments ─────────────────────────────────────────────────
OUT=""
BUFFER_SIZE=67108864   # 64 MiB default
CPU_ID=0
MEM_NODE=0
MODE="bandwidth_read"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --buffer_size) BUFFER_SIZE="$2"; shift 2 ;;
        --cpu_id)      CPU_ID="$2";      shift 2 ;;
        --mem_node)    MEM_NODE="$2";    shift 2 ;;
        --mode)        MODE="$2";        shift 2 ;;
        --out)         OUT="$2";         shift 2 ;;
        *)             shift 2 ;;        # skip unknown pairs
    esac
done

if [[ -z "$OUT" ]]; then
    echo "Error: --out <path> is required" >&2
    exit 1
fi

# ── Validate ────────────────────────────────────────────────────────
if ! command -v numactl &>/dev/null; then
    echo "Error: numactl is not installed (apt install numactl)" >&2
    exit 1
fi

N_CPUS=$(nproc)
if (( CPU_ID >= N_CPUS )); then
    echo "Error: cpu_id $CPU_ID but system only has $N_CPUS CPUs (0-$(( N_CPUS - 1 )))" >&2
    exit 1
fi

NUMA_NODES=$(numactl --hardware 2>/dev/null | grep -c '^node [0-9]* cpus:' || echo 1)
if (( MEM_NODE >= NUMA_NODES )); then
    echo "Error: mem_node $MEM_NODE but system has $NUMA_NODES NUMA node(s)" >&2
    exit 1
fi

# ── Resolve which NUMA node this CPU belongs to ─────────────────────
CPU_NODE=$(numactl --hardware 2>/dev/null \
    | awk -v cpu="$CPU_ID" '
        /^node [0-9]+ cpus:/ {
            node = $2
            for (i = 4; i <= NF; i++)
                if ($i == cpu) { print node; exit }
        }')
if [[ -z "$CPU_NODE" ]]; then
    CPU_NODE=0   # fallback for single-node systems
fi

# ── Determine crossing type ─────────────────────────────────────────
if [[ "$CPU_NODE" == "$MEM_NODE" ]]; then
    CROSSING="local"
else
    CROSSING="remote"
fi

# ── Run benchmark ───────────────────────────────────────────────────
echo "  cpu_id=$CPU_ID (node $CPU_NODE)  mem_node=$MEM_NODE  mode=$MODE  buffer=$(( BUFFER_SIZE / 1024 / 1024 ))MiB  $CROSSING" >&2

RAW=$(numactl --physcpubind="$CPU_ID" --membind="$MEM_NODE" \
      "$BENCH_BIN" -m "$MODE" -b "$BUFFER_SIZE")

VALUE=$(echo "$RAW" | awk '{print $1}')

# ── Write JSON result ───────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"

if [[ "$MODE" == "latency" ]]; then
    BW=0
    LAT=$VALUE
    echo "  -> latency=${VALUE} ns  ($CROSSING)" >&2
else
    BW=$VALUE
    LAT=0
    echo "  -> bandwidth=${VALUE} MiB/s  ($CROSSING)" >&2
fi

cat > "$OUT" <<EOF
{
  "bandwidth_mib_s": $BW,
  "latency_ns": $LAT
}
EOF
