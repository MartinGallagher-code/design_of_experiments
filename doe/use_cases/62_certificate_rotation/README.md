# Use Case 62: Certificate Rotation Strategy

## Scenario

You are automating Let's Encrypt ECDSA certificate rotation across a fleet of services and need to maximize rotation success rate while minimizing downtime during renewal. Shorter certificate lifetimes improve security posture but increase rotation frequency and failure risk, while the renewal window and OCSP stapling cache duration affect how gracefully rotations handle transient CA outages. A full factorial design with 3 factors exhaustively tests all combinations to reveal these interactions.

**This use case demonstrates:**
- Full Factorial design
- Multi-response analysis (rotation_success_rate, downtime_sec)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| cert_lifetime_days | 30 | 90 | days | Certificate validity lifetime |
| renewal_window_pct | 10 | 30 | % | Renewal window as percentage of lifetime |
| stapling_cache_sec | 300 | 3600 | sec | OCSP stapling cache duration |

**Fixed:** ca = letsencrypt, key_type = ecdsa_p256

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| rotation_success_rate | maximize | % |
| downtime_sec | minimize | sec |

## Why Full Factorial?

- Tests every combination of factor levels, ensuring no interaction is missed
- Ideal when the number of factors is small (2--4) and runs are affordable
- Provides complete information about main effects and all interaction effects
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template certificate_rotation
cd certificate_rotation
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
