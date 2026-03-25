#!/usr/bin/env bash
# Simulated GPU kernel benchmark — produces gflops and occupancy.
#
# Hidden model:
#   gflops ~ 500 (fp32) / 250 (fp64) base, boosted by larger block_size and unroll,
#            reduced by high shared_mem (limits active warps)
#   occupancy ~ 70% base, reduced by larger block_size and shared_mem
#              (fewer blocks can be resident)

set -euo pipefail

OUTFILE=""
BLOCK_SIZE=""
SHARED_MEM=""
UNROLL_FACTOR=""
PRECISION=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out)            OUTFILE="$2";       shift 2 ;;
        --block_size)     BLOCK_SIZE="$2";    shift 2 ;;
        --shared_mem)     SHARED_MEM="$2";    shift 2 ;;
        --unroll_factor)  UNROLL_FACTOR="$2"; shift 2 ;;
        --precision)      PRECISION="$2";     shift 2 ;;
        --gpu_model)      shift 2 ;;
        --problem_size)   shift 2 ;;
        *)                shift ;;
    esac
done

if [[ -z "$OUTFILE" || -z "$BLOCK_SIZE" || -z "$SHARED_MEM" || -z "$UNROLL_FACTOR" || -z "$PRECISION" ]]; then
    echo "Usage: sim.sh --block_size V --shared_mem V --unroll_factor V --precision V --out FILE" >&2
    exit 1
fi

RESULT=$(awk -v bs="$BLOCK_SIZE" -v sm="$SHARED_MEM" -v uf="$UNROLL_FACTOR" \
             -v prec="$PRECISION" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    noise1 = (rand() - 0.5) * 30;
    noise2 = (rand() - 0.5) * 5;

    # GFLOPS model
    if (prec == "fp32") base_gf = 500; else base_gf = 250;
    # Larger blocks improve instruction throughput
    gf = base_gf + (bs - 128) / 384.0 * 120;
    # Higher unroll boosts ILP
    gf += (uf - 2) / 6.0 * 80;
    # High shared memory limits active warps, reducing throughput
    gf -= (sm - 16) / 32.0 * 60;
    # Interaction: big blocks + high shared mem is especially bad
    gf -= (bs - 128) / 384.0 * (sm - 16) / 32.0 * 40;
    gf += noise1;
    if (gf < 50) gf = 50;

    # Occupancy model (%)
    occ = 70.0;
    # Larger blocks reduce occupancy (fewer fit per SM)
    occ -= (bs - 128) / 384.0 * 18;
    # More shared mem reduces occupancy
    occ -= (sm - 16) / 32.0 * 22;
    # Unroll has minor positive effect (better scheduling)
    occ += (uf - 2) / 6.0 * 5;
    # fp64 slightly lower occupancy (register pressure)
    if (prec == "fp64") occ -= 4;
    occ += noise2;
    if (occ < 10) occ = 10;
    if (occ > 100) occ = 100;

    printf "{\"gflops\": %.1f, \"occupancy\": %.1f}", gf, occ;
}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"

echo "  -> $(cat "$OUTFILE")"
