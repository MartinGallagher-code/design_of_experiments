# Use Case 52: VPN Tunnel MTU

## Scenario

You are configuring a WireGuard VPN tunnel with ChaCha20 encryption for remote site connectivity over unreliable WAN links. You need to balance tunnel MTU, fragment size, and keepalive interval to maximize sustained throughput while minimizing reconnect time after drops. A Box-Behnken design is appropriate because MTU and fragmentation interact nonlinearly -- too-large MTU causes packet drops while too-small MTU wastes bandwidth on headers -- and you need a quadratic model to find the sweet spot.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (throughput_mbps, reconnect_time_s)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| tunnel_mtu | 1200 | 1500 | bytes | VPN tunnel MTU |
| fragment_size | 0 | 1400 | bytes | Fragment size (0=disabled) |
| keepalive_interval | 10 | 120 | s | Tunnel keepalive interval |

**Fixed:** protocol = wireguard, encryption = chacha20

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_mbps | maximize | Mbps |
| reconnect_time_s | minimize | s |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template vpn_tunnel_mtu
cd vpn_tunnel_mtu
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
