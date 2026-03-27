# Use Case 63: IDS Signature Tuning

## Scenario

You are tuning a Suricata IDS running the Emerging Threats Open ruleset on a high-traffic network segment, where the goal is to maximize signature detection accuracy without dropping packets under load. The central tension is inspection depth versus throughput: loading more signatures and increasing pattern-match and stream-reassembly depths catches evasive attacks hidden deep in payloads, but the added per-packet processing causes the capture ring buffer to overflow, silently dropping traffic. A Latin Hypercube design efficiently explores the 4-parameter space of signature pool size, pattern-match depth, stream reassembly depth, and pcap buffer size without assuming how these resource-bound factors interact.

**This use case demonstrates:**
- Latin Hypercube design
- Multi-response analysis (detection_accuracy_pct, packet_drop_rate)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| signature_pool_size | 1000 | 50000 | sigs | Active signature pool size |
| pattern_match_depth | 256 | 4096 | bytes | Pattern matching inspection depth |
| stream_reassembly_depth | 4096 | 65536 | bytes | TCP stream reassembly depth |
| pcap_buffer_mb | 64 | 1024 | MB | Packet capture ring buffer size |

**Fixed:** ids_engine = suricata, ruleset = et_open

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| detection_accuracy_pct | maximize | % |
| packet_drop_rate | minimize | % |

## Why Latin Hypercube?

- A space-filling design that ensures each factor level is sampled exactly once per stratum
- Makes no assumptions about the underlying model form, ideal for computer experiments
- Provides good coverage of the entire factor space with a relatively small number of runs
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template ids_signature_tuning
cd ids_signature_tuning
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
