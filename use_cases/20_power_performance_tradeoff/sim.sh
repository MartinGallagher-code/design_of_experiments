#!/usr/bin/env bash
# =============================================================================
# sim.sh — Power-capping & performance trade-off simulator
#
# Simulates sustained GFLOPS and energy efficiency (GFLOPS/W) for an HPL
# workload on a 4-node GPU-accelerated HPC cluster under varying power caps
# and memory frequency settings.
#
# Usage:
#   bash sim.sh --out <dir> --cpu_power_cap <W> --gpu_power_cap <W> \
#               --mem_freq <MHz> [--cpu_model ...] [--gpu_model ...] \
#               [--nodes ...] [--workload ...]
# =============================================================================
set -euo pipefail

# ── Parse arguments ──────────────────────────────────────────────────────────
OUT_FILE=""
CPU_POWER_CAP=""
GPU_POWER_CAP=""
MEM_FREQ=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUT_FILE="$2";       shift 2 ;;
        --cpu_power_cap)  CPU_POWER_CAP="$2";  shift 2 ;;
        --gpu_power_cap)  GPU_POWER_CAP="$2";  shift 2 ;;
        --mem_freq)       MEM_FREQ="$2";       shift 2 ;;
        # Silently consume fixed factors
        --cpu_model|--gpu_model|--nodes|--workload)
                          shift 2 ;;
        *) echo "WARNING: unknown arg $1" >&2; shift ;;
    esac
done

if [[ -z "$OUT_FILE" || -z "$CPU_POWER_CAP" || -z "$GPU_POWER_CAP" || -z "$MEM_FREQ" ]]; then
    echo "ERROR: --out, --cpu_power_cap, --gpu_power_cap, and --mem_freq are required" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT_FILE")"

# ── Deterministic seed from inputs ───────────────────────────────────────────
SEED=$(echo "${CPU_POWER_CAP}_${GPU_POWER_CAP}_${MEM_FREQ}" | cksum | awk '{print $1}')
RANDOM=$((SEED % 32768))

# ── Helper: pseudo-random noise in [-scale, +scale] ─────────────────────────
noise() {
    local scale="$1"
    local r=$((RANDOM % 2001 - 1000))   # range -1000..1000
    echo "scale=6; $r / 1000 * $scale" | bc -l
}

# ── Normalise factors to [0, 1] ─────────────────────────────────────────────
#   cpu_power_cap : 120 – 240 W
#   gpu_power_cap : 200 – 400 W
#   mem_freq      : 2400 – 3200 MHz
x_cpu=$(echo "scale=6; ($CPU_POWER_CAP - 120) / 120" | bc -l)
x_gpu=$(echo "scale=6; ($GPU_POWER_CAP - 200) / 200" | bc -l)
x_mem=$(echo "scale=6; ($MEM_FREQ - 2400) / 800"     | bc -l)

# ── GFLOPS model ─────────────────────────────────────────────────────────────
# Base performance ~18 000 GFLOPS at the low corner.
# Contributions (with diminishing returns via sqrt-like saturation):
#   CPU power  → ~20 % of headroom  (≈ 3 600 GFLOPS at max)
#   GPU power  → ~65 % of headroom  (≈11 700 GFLOPS at max)
#   Mem freq   → ~15 % of headroom  (≈ 2 700 GFLOPS at max)
# Total theoretical max ≈ 36 000 GFLOPS.  Diminishing returns modelled by
# raising normalised factor to 0.7 (concave curve).
HEADROOM=18000
GFLOPS=$(echo "scale=4;
    base   = 18000;
    c_cpu  = 0.20 * $HEADROOM * e(0.7 * l($x_cpu + 0.01)) / e(0.7 * l(1.01));
    c_gpu  = 0.65 * $HEADROOM * e(0.7 * l($x_gpu + 0.01)) / e(0.7 * l(1.01));
    c_mem  = 0.15 * $HEADROOM * e(0.7 * l($x_mem + 0.01)) / e(0.7 * l(1.01));
    inter  = -0.04 * $HEADROOM * $x_cpu * $x_gpu;
    base + c_cpu + c_gpu + c_mem + inter
" | bc -l)

GFLOPS_NOISE=$(noise 250)
GFLOPS=$(echo "scale=2; $GFLOPS + $GFLOPS_NOISE" | bc -l)

# ── Total system power estimate (W) ─────────────────────────────────────────
# 4 nodes, each: CPU cap + 4 GPUs at gpu_cap + memory + overhead
TOTAL_POWER=$(echo "scale=2;
    nodes    = 4;
    per_node = $CPU_POWER_CAP + 4 * $GPU_POWER_CAP + ($MEM_FREQ / 3200) * 60 + 150;
    nodes * per_node
" | bc -l)

# ── GFLOPS-per-watt ─────────────────────────────────────────────────────────
# Efficiency = GFLOPS / total_power.  Peaks at moderate power levels because
# performance saturates while power grows linearly.
GFLOPS_PER_WATT=$(echo "scale=4; $GFLOPS / $TOTAL_POWER" | bc -l)

# Round to 2 decimal places
GFLOPS_PER_WATT=$(echo "scale=2; $GFLOPS_PER_WATT / 1" | bc -l)

# ── Write results ────────────────────────────────────────────────────────────
cat > "$OUT_FILE" <<EOF
{
    "gflops": ${GFLOPS},
    "gflops_per_watt": ${GFLOPS_PER_WATT}
}
EOF

echo "Results written to $OUT_FILE"
