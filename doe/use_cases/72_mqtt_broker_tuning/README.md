# Use Case 72: MQTT Broker Tuning

## Scenario

You are tuning a Mosquitto MQTT v5 broker serving thousands of IoT devices, aiming to maximize message throughput while keeping broker memory consumption within the limits of an edge gateway. The key trade-off is capacity versus resource usage: allowing more concurrent connections with deep per-client message queues sustains burst traffic but can exhaust memory, while higher QoS levels (0 vs. 1 vs. 2) add delivery guarantees at the cost of additional round-trips and state tracking per message. A Latin Hypercube design efficiently covers the 4-parameter space of connection limits, queue depth, keepalive interval, and QoS level without presupposing the response surface shape.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (message_throughput_kps, memory_usage_mb)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| max_connections | 100 | 10000 | conns | Maximum concurrent connections |
| message_queue_depth | 100 | 5000 | msgs | Per-client message queue depth |
| keepalive_sec | 15 | 300 | sec | Client keepalive interval |
| qos_level | 0 | 2 |  | MQTT QoS level |

**Fixed:** broker = mosquitto, protocol = mqtt_v5

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| message_throughput_kps | maximize | kmsg/s |
| memory_usage_mb | minimize | MB |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template mqtt_broker_tuning
cd mqtt_broker_tuning
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
