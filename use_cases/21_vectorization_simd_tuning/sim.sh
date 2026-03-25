#!/usr/bin/env bash
# ============================================================================
# SIMD Vectorization Tuning Simulator
# ============================================================================
# Simulates sustained GFLOPS and vectorization percentage for a 7-point
# stencil kernel under varying SIMD width, data layout, unroll factor,
# and alignment strategies.
# ============================================================================

set -euo pipefail

# ---- Parse arguments -------------------------------------------------------
OUT=""
SIMD_WIDTH=""
DATA_LAYOUT=""
UNROLL_FACTOR=""
ALIGNMENT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUT="$2";            shift 2 ;;
        --simd_width)     SIMD_WIDTH="$2";     shift 2 ;;
        --data_layout)    DATA_LAYOUT="$2";    shift 2 ;;
        --unroll_factor)  UNROLL_FACTOR="$2";  shift 2 ;;
        --alignment)      ALIGNMENT="$2";      shift 2 ;;
        *)                shift ;;  # ignore fixed factors and unknowns
    esac
done

if [[ -z "$OUT" ]]; then
    echo "Error: --out is required" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT")"

# ---- Helper: seeded pseudo-random noise ------------------------------------
# Generates a small random float in [-mag, +mag] using $RANDOM.
noise() {
    local mag="$1"
    local raw=$((RANDOM % 1000))
    awk -v r="$raw" -v m="$mag" 'BEGIN { printf "%.4f", (r / 500.0 - 1.0) * m }'
}

# Seed RANDOM from the factor combination for some run-to-run variation
SEED_STR="${SIMD_WIDTH}${DATA_LAYOUT}${UNROLL_FACTOR}${ALIGNMENT}"
HASH=$(echo -n "$SEED_STR" | cksum | awk '{print $1}')
RANDOM=$((HASH % 32768))

# ---- Compute GFLOPS --------------------------------------------------------
# Base throughput
gflops_base=80.0

# Main effects
gflops_simd=0.0
if [[ "$SIMD_WIDTH" == "512" ]]; then
    gflops_simd=35.0
fi

gflops_layout=0.0
if [[ "$DATA_LAYOUT" == "SoA" ]]; then
    gflops_layout=25.0
fi

gflops_unroll=0.0
if [[ "$UNROLL_FACTOR" == "8" ]]; then
    gflops_unroll=15.0
fi

gflops_align=0.0
if [[ "$ALIGNMENT" == "64B" ]]; then
    gflops_align=12.0
fi

# Interaction effects
gflops_soa_512=0.0
if [[ "$DATA_LAYOUT" == "SoA" && "$SIMD_WIDTH" == "512" ]]; then
    gflops_soa_512=10.0
fi

gflops_align_512=0.0
if [[ "$ALIGNMENT" == "64B" && "$SIMD_WIDTH" == "512" ]]; then
    gflops_align_512=8.0
fi

gflops_noise=$(noise 2.5)

gflops=$(awk -v base="$gflops_base" \
             -v simd="$gflops_simd" \
             -v layout="$gflops_layout" \
             -v unroll="$gflops_unroll" \
             -v align="$gflops_align" \
             -v soa512="$gflops_soa_512" \
             -v align512="$gflops_align_512" \
             -v noise="$gflops_noise" \
             'BEGIN { printf "%.2f", base + simd + layout + unroll + align + soa512 + align512 + noise }')

# ---- Compute vectorization percentage --------------------------------------
vec_base=60.0

vec_layout=0.0
if [[ "$DATA_LAYOUT" == "SoA" ]]; then
    vec_layout=18.0
fi

vec_simd=0.0
if [[ "$SIMD_WIDTH" == "512" ]]; then
    vec_simd=8.0
fi

vec_align=0.0
if [[ "$ALIGNMENT" == "64B" ]]; then
    vec_align=7.0
fi

vec_unroll=0.0
if [[ "$UNROLL_FACTOR" == "8" ]]; then
    vec_unroll=5.0
fi

# Interaction: SoA + alignment
vec_soa_align=0.0
if [[ "$DATA_LAYOUT" == "SoA" && "$ALIGNMENT" == "64B" ]]; then
    vec_soa_align=4.0
fi

vec_noise=$(noise 1.5)

vectorization_pct=$(awk -v base="$vec_base" \
                        -v layout="$vec_layout" \
                        -v simd="$vec_simd" \
                        -v align="$vec_align" \
                        -v unroll="$vec_unroll" \
                        -v soa_align="$vec_soa_align" \
                        -v noise="$vec_noise" \
                        'BEGIN {
                            val = base + layout + simd + align + unroll + soa_align + noise
                            if (val > 100.0) val = 100.0
                            printf "%.2f", val
                        }')

# ---- Write JSON output ------------------------------------------------------
cat > "$OUT" <<EOF
{
    "gflops": ${gflops},
    "vectorization_pct": ${vectorization_pct}
}
EOF

echo "Run complete: gflops=${gflops}, vectorization_pct=${vectorization_pct}%"
