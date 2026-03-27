# Use Case 49: Firewall Rule Ordering

## Scenario

You are hardening a Linux gateway handling a mix of 80% TCP and 20% UDP traffic, and packet processing performance is degrading as rule sets grow. There are 6 parameters to investigate -- rule count, conntrack table size, rule ordering strategy, hashlimit burst, firewall framework (iptables vs nftables), and batch verdict processing. A Plackett-Burman screening design identifies which of these factors most impact packet throughput and per-packet latency in just 8 runs, before you invest in a detailed optimization.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (throughput_mpps, latency_us)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| rule_count | 100 | 5000 | rules | Total number of firewall rules |
| conntrack_max | 65536 | 1048576 | entries | Connection tracking table size |
| rule_ordering | frequency | sequential |  | Rule evaluation ordering strategy |
| hashlimit_burst | 5 | 100 | packets | Hashlimit burst size |
| nf_tables | iptables | nftables |  | Firewall framework |
| batch_verdict | off | on |  | Batch verdict processing |

**Fixed:** interface = eth0, protocol_mix = 80_tcp_20_udp

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_mpps | maximize | Mpps |
| latency_us | minimize | us |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template firewall_rule_ordering
cd firewall_rule_ordering
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
