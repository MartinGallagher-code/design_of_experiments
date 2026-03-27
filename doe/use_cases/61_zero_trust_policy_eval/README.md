# Use Case 61: Zero Trust Policy Evaluation

## Scenario

You are implementing a zero trust architecture using Okta and Open Policy Agent, and need to balance authentication latency against security posture. There are 5 policy parameters to tune -- cache TTL, context attributes evaluated, risk score weighting, session timeout, and MFA frequency -- where stronger security (more attributes, shorter sessions, frequent MFA) directly increases user-facing latency. A fractional factorial design efficiently screens which of these controls most impact the security-versus-latency trade-off.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (auth_latency_ms, security_score)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| policy_cache_ttl | 10 | 300 | sec | Policy decision cache TTL |
| context_attributes | 3 | 12 | count | Number of context attributes evaluated |
| risk_score_weight | 0.1 | 0.9 | weight | Risk score weight in policy decision |
| session_timeout | 300 | 3600 | sec | Session timeout duration |
| mfa_frequency | 1 | 24 | hours | MFA re-authentication frequency |

**Fixed:** identity_provider = okta, policy_engine = opa

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| auth_latency_ms | minimize | ms |
| security_score | maximize | score |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template zero_trust_policy_eval
cd zero_trust_policy_eval
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
