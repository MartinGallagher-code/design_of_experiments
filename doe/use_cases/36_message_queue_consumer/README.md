# Use Case 36: Message Queue Consumer Tuning

## Scenario

You are tuning an Apache Kafka consumer group reading from a 12-partition topic with replication factor 3, aiming to maximize throughput while keeping consumer lag low enough for near-real-time processing. The fundamental tension is between batching efficiency and latency: large fetch sizes and high max-poll-records improve throughput but let lag accumulate during consumer rebalances, while too many consumers can exceed the partition count and sit idle. A Latin Hypercube design efficiently explores the 4-dimensional space of fetch size, poll records, consumer count, and session timeout without presupposing how these parameters interact.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (throughput_mbps, consumer_lag)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| fetch_min_bytes | 1 | 1048576 | bytes | Minimum fetch size |
| max_poll_records | 100 | 5000 | records | Max records per poll |
| num_consumers | 1 | 12 | count | Consumer group size |
| session_timeout | 6000 | 45000 | ms | Session timeout |

**Fixed:** partitions = 12, replication_factor = 3

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_mbps | maximize | MB/s |
| consumer_lag | minimize | records |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template message_queue_consumer
cd message_queue_consumer
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
