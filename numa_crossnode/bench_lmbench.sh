#!/usr/bin/env bash
# NUMA cross-node memory benchmark runner using lmbench.
#
# Called by the DOE harness with double-dash arguments:
#   ./bench_lmbench.sh --buffer_size 67108864 --cpu_id 0 --mem_node 1 \
#                      --mode bandwidth_read --out results/run_1.json
#
# Uses lmbench tools:
#   bw_mem      – sequential read/write bandwidth
#   lat_mem_rd  – pointer-chase memory read latency
#
# Requires: numactl, lmbench (bw_mem, lat_mem_rd on PATH)

set -euo pipefail

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

# ── Check prerequisites ────────────────────────────────────────────
for cmd in numactl bw_mem lat_mem_rd; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is not installed" >&2
        exit 1
    fi
done

# ── Validate ────────────────────────────────────────────────────────
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
    CPU_NODE=0
fi

if [[ "$CPU_NODE" == "$MEM_NODE" ]]; then
    CROSSING="local"
else
    CROSSING="remote"
fi

# ── Convert buffer size to MB for lmbench ───────────────────────────
# lmbench expects size in MB (megabytes, base-10 for bw_mem, but it
# actually interprets the argument as bytes when suffixed, or as MB
# otherwise).  We pass raw bytes and let lmbench handle it via the 'm'
# suffix, or convert to MB.
BUFFER_MB=$(awk "BEGIN {printf \"%.4f\", $BUFFER_SIZE / 1048576}")

echo "  cpu_id=$CPU_ID (node $CPU_NODE)  mem_node=$MEM_NODE  mode=$MODE  buffer=${BUFFER_MB}MiB  $CROSSING" >&2

# ── Run lmbench ─────────────────────────────────────────────────────
NUMA_CMD="numactl --physcpubind=$CPU_ID --membind=$MEM_NODE"

BW=0
LAT=0

case "$MODE" in
    bandwidth_read)
        # bw_mem <size> rd  →  outputs: <size> <bandwidth MB/s>
        RAW=$($NUMA_CMD bw_mem "${BUFFER_SIZE}" rd 2>/dev/null | tail -1)
        BW=$(echo "$RAW" | awk '{printf "%.4f", $2}')
        echo "  -> bandwidth=${BW} MiB/s  ($CROSSING)" >&2
        ;;
    bandwidth_write)
        # bw_mem <size> wr  →  outputs: <size> <bandwidth MB/s>
        RAW=$($NUMA_CMD bw_mem "${BUFFER_SIZE}" wr 2>/dev/null | tail -1)
        BW=$(echo "$RAW" | awk '{printf "%.4f", $2}')
        echo "  -> bandwidth=${BW} MiB/s  ($CROSSING)" >&2
        ;;
    latency)
        # lat_mem_rd <size_MB> <stride>
        # Outputs multiple lines: <size> <latency_ns>
        # We take the last line (largest working set = steady-state latency)
        RAW=$($NUMA_CMD lat_mem_rd "${BUFFER_MB}" 64 2>/dev/null | grep -v '^"' | tail -1)
        LAT=$(echo "$RAW" | awk '{printf "%.4f", $2}')
        echo "  -> latency=${LAT} ns  ($CROSSING)" >&2
        ;;
    *)
        echo "Error: unknown mode '$MODE' (expected: bandwidth_read, bandwidth_write, latency)" >&2
        exit 1
        ;;
esac

# ── Write JSON result ───────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"

cat > "$OUT" <<EOF
{
  "bandwidth_mib_s": $BW,
  "latency_ns": $LAT
}
EOF
