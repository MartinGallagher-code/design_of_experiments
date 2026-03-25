#!/bin/bash
# Cache Blocking Strategy Simulator
# Simulates DGEMM performance (GFLOPS) and cache miss rate for tile/block sizes.
# Usage: bash sim.sh --block_i 64 --block_j 64 --block_k 64 --prefetch_dist 4 --out results.json

# Defaults
block_i=64
block_j=64
block_k=64
prefetch_dist=4
out="result.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --block_i) block_i="$2"; shift 2 ;;
    --block_j) block_j="$2"; shift 2 ;;
    --block_k) block_k="$2"; shift 2 ;;
    --prefetch_dist) prefetch_dist="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Compute gflops and cache_miss_rate
read gflops cache_miss_rate <<< $(awk \
  -v bi="$block_i" -v bj="$block_j" -v bk="$block_k" -v pd="$prefetch_dist" '
BEGIN {
  srand(systime() + bi + bj * 3 + bk * 7);
  noise_g = (rand() - 0.5) * 3.0;
  noise_c = (rand() - 0.5) * 1.5;

  # Optimal block size is around 64-128 for L2 cache fitting
  # GFLOPS peaks when blocks fit in cache, drops at extremes
  # Model each dimension with a Gaussian-like response centered at ~96

  opt = 96;
  sigma = 70;

  fi = exp(-((bi - opt)^2) / (2 * sigma^2));
  fj = exp(-((bj - opt)^2) / (2 * sigma^2));
  fk = exp(-((bk - opt)^2) / (2 * sigma^2));

  # Prefetch helps moderately, best around 3-5
  fp = 1 - 0.04 * (pd - 4)^2;
  if (fp < 0.7) fp = 0.7;

  # Peak GFLOPS around 85 for dual-socket Xeon (single DGEMM kernel)
  gflops = 85.0 * fi * fj * fk * fp + noise_g;
  if (gflops < 8) gflops = 8;
  if (gflops > 90) gflops = 90;

  # Cache miss rate: lowest at mid-range blocks (fit in L2/L3)
  # Very small blocks = overhead; very large blocks = thrash cache
  mi = 1 - exp(-((bi - 96)^2) / (2 * 80^2)) * 0.7;
  mj = 1 - exp(-((bj - 96)^2) / (2 * 80^2)) * 0.7;
  mk = 1 - exp(-((bk - 96)^2) / (2 * 80^2)) * 0.7;

  # Prefetch reduces miss rate
  pf_benefit = 1 - 0.03 * pd;

  cache_miss = 12.0 * (mi + mj + mk) / 3.0 * pf_benefit + noise_c;
  if (cache_miss < 0.5) cache_miss = 0.5;
  if (cache_miss > 35) cache_miss = 35;

  printf "%.2f %.2f\n", gflops, cache_miss;
}')

# Write JSON output
cat > "$out" <<EOF
{
  "gflops": ${gflops},
  "cache_miss_rate": ${cache_miss_rate},
  "parameters": {
    "block_i": ${block_i},
    "block_j": ${block_j},
    "block_k": ${block_k},
    "prefetch_dist": ${prefetch_dist},
    "matrix_size": 4096,
    "algorithm": "dgemm"
  }
}
EOF

echo "Results written to $out"
