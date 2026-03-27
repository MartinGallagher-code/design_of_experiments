# Use Case 51: BGP Route Convergence

## Scenario

You are tuning BGP timer and dampening settings across a 50-AS partial-mesh network to speed up route convergence after link failures while maintaining route stability. Aggressive keepalive and MRAI timers reduce convergence time but can cause route flapping, while dampening suppresses flaps at the cost of slower recovery. A fractional factorial design efficiently screens these 5 interdependent parameters to find the dominant factors without exhaustive testing.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (convergence_time_s, route_stability)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| keepalive_s | 10 | 60 | s | BGP keepalive interval |
| hold_time_s | 30 | 180 | s | BGP hold time |
| mrai_s | 5 | 30 | s | Minimum route advertisement interval |
| dampening | off | on |  | Route flap dampening |
| bfd | off | on |  | Bidirectional forwarding detection |

**Fixed:** as_count = 50, topology = partial_mesh

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| convergence_time_s | minimize | s |
| route_stability | maximize | % |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template bgp_route_convergence
cd bgp_route_convergence
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
