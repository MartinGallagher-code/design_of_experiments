# Use Case 59: SIEM Alert Correlation

## Scenario

You are configuring alert correlation rules in Elastic Security to reduce alert fatigue from 12 log sources without missing real security incidents. You need to tune the correlation time window, similarity threshold, and minimum event count -- too aggressive and you merge unrelated alerts (missing incidents), too conservative and analysts are overwhelmed. A Box-Behnken design models the nonlinear relationship between these thresholds and alert reduction, avoiding extreme corners where correlation could either collapse all alerts or have no effect.

**This use case demonstrates:**
- Box-Behnken design
- Multi-response analysis (alert_reduction_pct, missed_incident_rate)
- Response Surface Methodology (RSM)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| correlation_window_sec | 30 | 600 | sec | Time window for correlating alerts |
| similarity_threshold | 0.3 | 0.9 | ratio | Similarity threshold for grouping |
| min_event_count | 2 | 10 | events | Minimum events to trigger correlation |

**Fixed:** siem_platform = elastic_security, log_sources = 12

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| alert_reduction_pct | maximize | % |
| missed_incident_rate | minimize | % |

## Why Box-Behnken?

- A 3-level RSM design that avoids running experiments at extreme corner conditions
- Fits full quadratic models, enabling prediction of curved response surfaces
- Requires fewer runs than a central composite design for 3--5 continuous factors
- We have 3 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template siem_alert_correlation
cd siem_alert_correlation
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
