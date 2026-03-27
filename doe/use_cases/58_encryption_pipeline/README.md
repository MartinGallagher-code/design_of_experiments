# Use Case 58: Encryption Pipeline Optimization

## Scenario

You are designing a TLS 1.3 encryption pipeline in GCM mode and need to maximize throughput while minimizing CPU overhead. The key question is how cipher suite choice, key size, pre-encryption compression, and AES-NI hardware acceleration interact -- for instance, compression may help throughput on compressible data but add CPU cost that offsets AES-NI gains. With only 4 two-level factors, a full factorial design tests every combination and reveals all interaction effects.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (throughput_mbps, cpu_overhead_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cipher_suite | aes128 | aes256 |  | Cipher suite selection |
| key_size | 128 | 256 | bits | Encryption key size |
| compression_before_encrypt | off | on |  | Compress before encryption |
| hardware_acceleration | off | on |  | AES-NI hardware acceleration |

**Fixed:** protocol = tls1.3, mode = gcm

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| throughput_mbps | maximize | Mbps |
| cpu_overhead_pct | minimize | % |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 4 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template encryption_pipeline
cd encryption_pipeline
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
