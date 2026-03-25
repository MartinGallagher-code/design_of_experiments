# CPU Frequency Governor & P-State Tuning

## Scenario

Modern HPC workloads alternate between compute-intensive phases (linear algebra,
FFTs) and memory-bound phases (sparse solvers, data shuffles).  The Linux CPU
frequency governor controls how aggressively the processor ramps frequency up or
down between these phases.  Choosing the wrong governor or misconfiguring P-state
limits can leave performance on the table or waste power without meaningful
throughput gains.

This use case applies a **Box-Behnken design with 3 factors** to find the
optimal CPU frequency governor configuration for a mixed compute/memory HPC
workload running on Intel Xeon 8490H (Sapphire Rapids, 56 cores, 350 W TDP).

### Factors

| # | Factor              | Levels                                   | Description                                        |
|---|---------------------|------------------------------------------|----------------------------------------------------|
| 1 | `governor`          | performance, schedutil, conservative     | Linux CPU frequency scaling governor               |
| 2 | `min_freq_pct`      | 40 % -- 80 %                             | Minimum frequency as a percentage of max turbo      |
| 3 | `energy_perf_bias`  | 0 -- 15                                  | Intel EPB hint (0 = max perf, 15 = max power save) |

### Responses

| Response                  | Goal     | Unit | Description                                          |
|---------------------------|----------|------|------------------------------------------------------|
| `throughput_normalized`   | maximize | %    | Application throughput relative to max-frequency run  |
| `energy_delay_product`    | minimize | J*s  | Energy-delay product -- balances power and latency    |

### Fixed conditions

- Processor: Intel Xeon 8490H (56 cores, 3.5 GHz max turbo, 350 W TDP)
- Workload: mixed compute/memory benchmark representative of production jobs
- Single-socket measurement to isolate frequency scaling effects

## Demonstrates

- **Box-Behnken design** -- efficient 3-factor design that avoids extreme corners
- **Frequency-performance scaling** -- non-linear relationship between clock speed and throughput
- **Energy-delay product optimization** -- single metric that captures the power/performance trade-off
- **Workload-phase-aware tuning** -- governor behavior matters most during phase transitions

## Quick start

```bash
# Generate the Box-Behnken design matrix
doe generate use_cases/25_cpu_frequency_governor/config.json

# Run the simulated experiment
doe run use_cases/25_cpu_frequency_governor/config.json

# Analyze results
doe analyze use_cases/25_cpu_frequency_governor/config.json
```

## What to look for

1. The `performance` governor yields the highest raw throughput but at a steep
   energy cost.  The `schedutil` governor often lands in the Pareto-optimal
   region when paired with a moderate `min_freq_pct`.
2. Very low `min_freq_pct` (40 %) hurts throughput during phase transitions
   because the governor cannot ramp fast enough.
3. The energy-delay product has a clear minimum at moderate EPB and min-frequency
   settings, confirming that neither extreme saves total cost.
