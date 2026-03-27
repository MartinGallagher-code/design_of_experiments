#!/bin/bash
# Copyright (C) 2026 Martin J. Gallagher, SageCor Solutions
# SPDX-License-Identifier: GPL-3.0-or-later
# Distributed Deep Learning Scaling Simulator
# Simulates multi-GPU training throughput and scaling efficiency for ResNet-50.
# Usage: bash sim.sh --gpu_count 32 --batch_per_gpu 128 --gradient_compression 50 --out results.json

# Defaults
gpu_count=16
batch_per_gpu=128
gradient_compression=0
out="result.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu_count) gpu_count="$2"; shift 2 ;;
    --batch_per_gpu) batch_per_gpu="$2"; shift 2 ;;
    --gradient_compression) gradient_compression="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Compute images_per_sec and scaling_efficiency
read images_per_sec scaling_efficiency <<< $(awk \
  -v gpus="$gpu_count" -v bpg="$batch_per_gpu" -v gc="$gradient_compression" '
BEGIN {
  srand(systime() + gpus * 100 + bpg);
  noise_i = (rand() - 0.5) * 40;
  noise_s = (rand() - 0.5) * 2.0;

  # Single-GPU baseline: ~320 img/s for ResNet-50 on A100 with batch=128
  single_gpu_base = 320;

  # Per-GPU throughput scales with batch size (diminishing returns)
  batch_factor = (bpg / 128)^0.6;
  per_gpu = single_gpu_base * batch_factor;

  # Communication overhead grows with GPU count (sublinear scaling)
  # Gradient compression reduces the communication cost
  comm_reduction = 1 - 0.6 * (gc / 100);  # compression helps
  comm_overhead = 0.003 * (gpus - 1) * comm_reduction;
  eff_factor = 1 / (1 + comm_overhead);

  images_per_sec = per_gpu * gpus * eff_factor + noise_i;
  if (images_per_sec < 500) images_per_sec = 500;

  # Scaling efficiency = actual throughput / (single_gpu * gpu_count) * 100
  ideal = per_gpu * gpus;
  scaling_efficiency = (images_per_sec / ideal) * 100 + noise_s;
  if (scaling_efficiency > 99) scaling_efficiency = 99;
  if (scaling_efficiency < 40) scaling_efficiency = 40;

  printf "%.1f %.1f\n", images_per_sec, scaling_efficiency;
}')

# Write JSON output
cat > "$out" <<EOF
{
  "images_per_sec": ${images_per_sec},
  "scaling_efficiency": ${scaling_efficiency},
  "parameters": {
    "gpu_count": ${gpu_count},
    "batch_per_gpu": ${batch_per_gpu},
    "gradient_compression": ${gradient_compression},
    "model": "resnet50",
    "dataset": "imagenet"
  }
}
EOF

echo "Results written to $out"
