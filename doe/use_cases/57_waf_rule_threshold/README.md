# Use Case 57: WAF Rule Threshold Tuning

## Scenario

You are tuning a ModSecurity WAF with the OWASP Core Rule Set to protect a production web application. The fundamental trade-off is between attack detection rate and false positive rate on legitimate traffic -- tightening thresholds catches more attacks but blocks real users. With 6 parameters to adjust (rate limits, body inspection depth, anomaly score threshold, paranoia level, SQLi sensitivity, and XSS detection level), a Plackett-Burman screening design identifies the most impactful knobs in just 8 runs.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (detection_rate, false_positive_rate)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| rate_limit_rps | 100 | 10000 | rps | Request rate limit per client |
| body_inspection_depth | 1000 | 65536 | bytes | Request body inspection depth |
| anomaly_score_threshold | 3 | 15 | score | Anomaly score blocking threshold |
| paranoia_level | 1 | 4 | level | CRS paranoia level |
| sql_injection_sensitivity | 1 | 9 | level | SQLi detection sensitivity |
| xss_detection_level | 1 | 5 | level | XSS detection sensitivity level |

**Fixed:** waf_engine = modsecurity, ruleset = owasp_crs

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| detection_rate | maximize | % |
| false_positive_rate | minimize | % |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template waf_rule_threshold
cd waf_rule_threshold
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
