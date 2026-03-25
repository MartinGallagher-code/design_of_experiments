# Use Case 11: InfiniBand Network Tuning

## Scenario

You are tuning an InfiniBand HDR (200 Gb/s) network fabric for a latency-sensitive HPC application. Three factors — MTU size, send/receive queue depth, and RDMA connection manager — affect both message throughput and tail latency. A Box-Behnken design with 3 factors provides 15 runs (including center points) and can fit a quadratic response surface to find the optimum operating point.

**This use case demonstrates:**
- Box-Behnken design (3 factors, avoids extreme corners)
- Quadratic response surface modeling for network parameters
- Trade-off between throughput (message rate) and tail latency (p99)
- InfiniBand-specific performance tuning

## Factors

| Factor | Low | High | Type | Unit | Description |
|--------|-----|------|------|------|-------------|
| mtu | 2048 | 4096 | continuous | bytes | Maximum transmission unit |
| queue_depth | 64 | 512 | continuous | | Send/receive queue depth |
| rdma_cm | on | off | categorical | | RDMA connection manager |

**Fixed:** ib_speed = HDR, ports = 1

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| msg_rate | maximize | Mmsg/s |
| p99_lat | minimize | us |

## Running the Demo

```bash
cd /workspaces/design_of_experiments
python doe.py info --config use_cases/11_infiniband_network/config.json
python doe.py generate --config use_cases/11_infiniband_network/config.json \
    --output use_cases/11_infiniband_network/results/run.sh --seed 42
bash use_cases/11_infiniband_network/results/run.sh
python doe.py analyze --config use_cases/11_infiniband_network/config.json
python doe.py report --config use_cases/11_infiniband_network/config.json \
    --output use_cases/11_infiniband_network/results/report.html
```

## Files

- Config: `use_cases/11_infiniband_network/config.json`
- Simulator: `use_cases/11_infiniband_network/sim.sh`
- Results: `use_cases/11_infiniband_network/results/`
