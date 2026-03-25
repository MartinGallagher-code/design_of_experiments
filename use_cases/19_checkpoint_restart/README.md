# Checkpoint/Restart I/O Optimization

## Scenario

Large-scale HPC simulations running on 1024 nodes must periodically write
checkpoint files so that work is not lost if the job fails or is preempted.
Each node contributes roughly 16 GB of state, producing a 16 TB aggregate
checkpoint.  The challenge is to push that data to persistent storage as fast
as possible while keeping the time the application is stalled to a minimum.

The system is equipped with a Lustre parallel filesystem and a DataWarp burst
buffer tier.  Three continuous factors govern checkpoint behavior:

| Factor | Range | Unit | Description |
|--------|-------|------|-------------|
| `checkpoint_interval` | 5 -- 30 | minutes | Time between successive checkpoint writes |
| `stripe_count` | 4 -- 64 | (count) | Lustre stripe count for checkpoint files |
| `bb_capacity_pct` | 25 -- 100 | % | Fraction of burst buffer capacity reserved for checkpoints |

A **Box-Behnken design** is used because it avoids extreme corner points
(all factors at their high or low levels simultaneously), which is desirable
here -- running with minimal stripes, minimal burst buffer, and very frequent
checkpoints at the same time could destabilize the storage subsystem.

## Demonstrates

* **Box-Behnken design** -- a three-level response-surface design for three
  continuous factors that requires fewer runs than a full three-level factorial.
* **Checkpoint I/O tuning** -- balancing Lustre striping and write frequency.
* **Burst buffer utilization** -- quantifying how much staging capacity to
  reserve for checkpoints vs. leaving it available for application scratch I/O.
* **Trade-off between checkpoint speed and application interference** -- the
  two responses (write throughput and application disruption time) are jointly
  optimized so that faster checkpoints do not come at the cost of unacceptable
  stalls.

## Responses

| Response | Goal | Unit |
|----------|------|------|
| `write_throughput_GBs` | maximize | GB/s |
| `app_disruption_sec` | minimize | seconds |

## Running

```bash
doe run --config use_cases/19_checkpoint_restart/config.json
```

After the experiment completes, analyze with:

```bash
doe analyze --config use_cases/19_checkpoint_restart/config.json
```
