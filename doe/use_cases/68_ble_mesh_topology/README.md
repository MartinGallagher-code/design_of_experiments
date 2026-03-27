# Use Case 68: BLE Mesh Topology

## Scenario

You are deploying a Bluetooth 5.0 SIG Mesh network for smart building lighting control and need to maximize message delivery reliability while minimizing network latency. More relay nodes and higher TTL hops improve delivery in large spaces but increase network flooding and latency, while faster publish intervals can overwhelm the mesh. A Box-Behnken design models these nonlinear trade-offs with fewer runs than a central composite design, avoiding extreme corners where the mesh could become saturated.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (message_delivery_pct, network_latency_ms)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| relay_count | 2 | 10 | nodes | Number of relay nodes in mesh |
| ttl_hops | 2 | 8 | hops | Message TTL in hops |
| publish_interval_ms | 100 | 2000 | ms | Message publish interval |

**Fixed:** ble_version = 5.0, mesh_profile = sig_mesh

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| message_delivery_pct | maximize | % |
| network_latency_ms | minimize | ms |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template ble_mesh_topology
cd ble_mesh_topology
```

### Step 2: Preview the design
```bash
doe info --config config.json
```

### Step 3: Generate and run
```bash
doe generate --config config.json --output results/run.sh --seed 42
bash results/run.sh
```

### Step 4: Analyze
```bash
doe analyze --config config.json
```

### Step 5: Optimize and report
```bash
doe optimize --config config.json
doe report --config config.json --output results/report.html
```
