#!/bin/bash
# Job Scheduler Packing Simulator
# Simulates throughput and efficiency for various scheduler packing configurations.
# Usage: bash sim.sh --nodes N --tasks_per_node T --mem_per_task M --out results.json

# Defaults
nodes=16
tasks_per_node=24
mem_per_task=4
out="result.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --nodes) nodes="$2"; shift 2 ;;
    --tasks_per_node) tasks_per_node="$2"; shift 2 ;;
    --mem_per_task) mem_per_task="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Compute throughput and efficiency using awk for floating-point math
read throughput efficiency <<< $(awk -v n="$nodes" -v tpn="$tasks_per_node" -v mpt="$mem_per_task" '
BEGIN {
  # Clamp inputs (CCD star points can go negative)
  if (n < 1) n = 1;
  if (tpn < 1) tpn = 1;
  if (mpt < 0.5) mpt = 0.5;

  srand(systime() + n * 1000 + tpn * 100 + mpt * 10);
  noise_t = (rand() - 0.5) * 4;
  noise_e = (rand() - 0.5) * 3;

  # Total cores = nodes * tasks_per_node
  total_tasks = n * tpn;

  # Throughput peaks at moderate tasks_per_node (~28), decreases with high mem
  # Base throughput scales with total tasks but with diminishing returns
  task_factor = (1 - ((tpn - 28) / 28)^2);  # peaks at 28
  mem_penalty = 1 - 0.08 * (mpt - 1);        # less mem = higher throughput
  node_scale = n^0.75;                        # sublinear scaling with nodes
  throughput = 12.5 * node_scale * task_factor * mem_penalty + noise_t;
  if (throughput < 5) throughput = 5;

  # Efficiency decreases with more nodes (communication overhead)
  # Best at low node count, moderate tasks_per_node
  comm_overhead = 1 - 0.005 * (n - 4);       # overhead grows with nodes
  task_eff = (1 - 0.4 * ((tpn - 28) / 40)^2);
  mem_eff = 1 - 0.03 * (mpt - 1);
  efficiency = 95 * comm_overhead * task_eff * mem_eff + noise_e;
  if (efficiency > 99) efficiency = 99;
  if (efficiency < 30) efficiency = 30;

  printf "%.2f %.2f\n", throughput, efficiency;
}')

# Write JSON output
cat > "$out" <<EOF
{
  "throughput": ${throughput},
  "efficiency": ${efficiency},
  "parameters": {
    "nodes": ${nodes},
    "tasks_per_node": ${tasks_per_node},
    "mem_per_task": ${mem_per_task},
    "partition": "compute",
    "walltime": "4h"
  }
}
EOF

echo "Results written to $out"
