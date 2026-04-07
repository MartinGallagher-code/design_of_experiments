#!/usr/bin/env bash
# Quick-start script for the NUMA cross-node benchmark.
#
# Detects the actual NUMA topology, patches config.json with the real
# CPU IDs and NUMA nodes, generates the DOE experiment, runs it, and
# analyses the results.
#
# Usage:
#   cd numa_crossnode && bash run.sh
#
# Prerequisites:
#   - numactl   (apt install numactl)
#   - gcc
#   - python3 with the doe package installed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$SCRIPT_DIR/config.json"

cd "$ROOT_DIR"

# ── Check prerequisites ─────────────────────────────────────────────
for cmd in numactl gcc python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is required but not found" >&2
        exit 1
    fi
done

# ── Detect NUMA topology ────────────────────────────────────────────
echo "=== NUMA Topology ==="
numactl --hardware
echo

NUMA_NODES=$(numactl --hardware | grep -c '^node [0-9]* cpus:')
echo "Detected $NUMA_NODES NUMA node(s)."

# Build list of NUMA node IDs and all CPU IDs
NODE_IDS=$(numactl --hardware | grep '^node [0-9]* cpus:' | awk '{print $2}' | tr '\n' ',' | sed 's/,$//')
ALL_CPU_IDS=$(numactl --hardware | grep '^node [0-9]* cpus:' | sed 's/node [0-9]* cpus://' | tr ' ' '\n' | grep -v '^$' | sort -n | tr '\n' ',' | sed 's/,$//')

echo "NUMA nodes: $NODE_IDS"
echo "CPU IDs:    $ALL_CPU_IDS"
echo

# ── Patch config.json with actual topology ───────────────────────────
python3 -c "
import json

with open('$CONFIG') as f:
    cfg = json.load(f)

node_ids = '$NODE_IDS'.split(',')
cpu_ids = '$ALL_CPU_IDS'.split(',')

for f in cfg['factors']:
    if f['name'] == 'cpu_id':
        f['levels'] = cpu_ids
    elif f['name'] == 'mem_node':
        f['levels'] = node_ids

with open('$CONFIG', 'w') as f:
    json.dump(cfg, f, indent=4)

n_runs = len(cpu_ids) * len(node_ids) * 7 * 3  # 7 buffer sizes, 3 modes
print(f'Config patched: {len(cpu_ids)} CPUs x {len(node_ids)} mem nodes x 7 sizes x 3 modes = {n_runs} runs')
"

# ── Generate experiment ──────────────────────────────────────────────
echo ""
echo "=== Generating Experiment ==="
python3 -m doe generate --config "$CONFIG" --output "$SCRIPT_DIR/run_experiments.sh"

# ── Run experiment ───────────────────────────────────────────────────
echo ""
echo "=== Running Benchmark ==="
bash "$SCRIPT_DIR/run_experiments.sh"

# ── Analyse results ──────────────────────────────────────────────────
echo ""
echo "=== Analysis ==="
python3 -m doe analyze --config "$CONFIG" --knee --partial

echo ""
echo "Done.  Results in: $SCRIPT_DIR/results/"
echo "HTML report:       $SCRIPT_DIR/results/analysis/report.html"
