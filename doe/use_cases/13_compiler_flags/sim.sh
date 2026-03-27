#!/bin/bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Compiler Optimization Flags Simulator
# Simulates execution time and binary size for various GCC flag combinations.
# Usage: bash sim.sh --opt_level O3 --vectorize avx512 --lto on --march native \
#                    --unroll on --fast_math off --pgo on --out results.json

# Defaults
opt_level="O2"
vectorize="off"
lto="off"
march="native"
unroll="off"
fast_math="off"
pgo="off"
out="result.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --opt_level) opt_level="$2"; shift 2 ;;
    --vectorize) vectorize="$2"; shift 2 ;;
    --lto) lto="$2"; shift 2 ;;
    --march) march="$2"; shift 2 ;;
    --unroll) unroll="$2"; shift 2 ;;
    --fast_math) fast_math="$2"; shift 2 ;;
    --pgo) pgo="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Compute exec_time and binary_size
read exec_time binary_size <<< $(awk \
  -v opt="$opt_level" -v vec="$vectorize" -v lto="$lto" -v march="$march" \
  -v unroll="$unroll" -v fm="$fast_math" -v pgo="$pgo" '
BEGIN {
  srand(systime());
  noise_t = (rand() - 0.5) * 2.0;
  noise_s = (rand() - 0.5) * 0.4;

  # Base execution time: ~120 seconds
  t = 120.0;

  # O3 reduces exec_time by ~10%
  if (opt == "O3") t = t * 0.90;

  # avx512 reduces exec_time by ~15%
  if (vec == "avx512") t = t * 0.85;

  # LTO reduces exec_time by ~8%
  if (lto == "on") t = t * 0.92;

  # znver3 gives slight improvement over native (~3%)
  if (march == "znver3") t = t * 0.97;

  # unroll has small effect (~2%)
  if (unroll == "on") t = t * 0.98;

  # fast_math reduces exec_time by ~12% (relaxed fp)
  if (fm == "on") t = t * 0.88;

  # PGO reduces exec_time by ~18%
  if (pgo == "on") t = t * 0.82;

  t = t + noise_t;

  # Base binary size: ~15 MB
  s = 15.0;

  # LTO increases binary size by ~20% (whole-program IR)
  if (lto == "on") s = s * 1.20;

  # unroll increases binary size by ~15%
  if (unroll == "on") s = s * 1.15;

  # PGO increases binary size by ~25% (profiling metadata + specialization)
  if (pgo == "on") s = s * 1.25;

  # O3 slightly increases size vs O2 (~5%)
  if (opt == "O3") s = s * 1.05;

  # avx512 wider instructions, slight increase (~3%)
  if (vec == "avx512") s = s * 1.03;

  s = s + noise_s;

  printf "%.2f %.2f\n", t, s;
}')

# Write JSON output
cat > "$out" <<EOF
{
  "exec_time": ${exec_time},
  "binary_size": ${binary_size},
  "parameters": {
    "opt_level": "${opt_level}",
    "vectorize": "${vectorize}",
    "lto": "${lto}",
    "march": "${march}",
    "unroll": "${unroll}",
    "fast_math": "${fast_math}",
    "pgo": "${pgo}",
    "compiler": "gcc13",
    "benchmark": "npb_bt"
  }
}
EOF

echo "Results written to $out"
