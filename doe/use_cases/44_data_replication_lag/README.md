# Use Case 44: Data Replication Lag

## Scenario

You are configuring MySQL 8 GTID-based replication for a high-availability database cluster. You need to minimize replication lag while keeping the replica within RPO for failover readiness, but there are 5 interacting parameters -- sync mode, binlog batch size, parallel applier workers, network buffer, and binlog compression. A fractional factorial design efficiently screens these factors to find which settings drive lag versus failover readiness without running all 32 combinations.

**This use case demonstrates:**
- Fractional Factorial design
- Multi-response analysis (replication_lag_ms, failover_ready_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| sync_mode | async | semi_sync |  | Replication sync mode |
| binlog_batch_size | 1 | 100 | txns | Binlog batch size |
| parallel_workers | 1 | 16 | threads | Replica applier workers |
| network_buffer_kb | 64 | 1024 | KB | Replication network buffer |
| compression | off | on |  | Binlog compression |

**Fixed:** engine = mysql_8, gtid = on

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| replication_lag_ms | minimize | ms |
| failover_ready_pct | maximize | % |

## Why Fractional Factorial?

- Tests only a fraction of all possible combinations, dramatically reducing the number of runs
- Well-suited for screening many factors (5+) when higher-order interactions are assumed negligible
- Efficiently identifies the most influential main effects and low-order interactions
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template data_replication_lag
cd data_replication_lag
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
