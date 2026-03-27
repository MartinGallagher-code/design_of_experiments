# Use Case 218: Soccer Passing Drill Design

## Scenario

You are designing a soccer passing drill on artificial turf and need to screen five drill parameters -- pass distance, player count, tempo, rest interval, and cone gate spacing -- to identify which ones most influence passing accuracy and decision-making speed. Practice time is limited and fatigue confounds long sessions, so you cannot afford to test all 32 factor combinations. A Plackett-Burman design screens all 5 factors in just 8 drill configurations, efficiently revealing which design knobs matter most before you invest in a detailed optimization.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (accuracy_pct, decision_speed_ms)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| pass_dist_m | 5 | 20 | m | Required pass distance |
| player_count | 4 | 10 | players | Number of players in drill |
| tempo_bpm | 60 | 120 | bpm | Drill tempo in beats per minute |
| rest_sec | 10 | 60 | sec | Rest between repetitions |
| cone_spacing_m | 2 | 8 | m | Cone gate spacing |

**Fixed:** ball_type = size_5, surface = artificial_turf

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| accuracy_pct | maximize | % |
| decision_speed_ms | minimize | ms |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template soccer_passing_drill
cd soccer_passing_drill
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
