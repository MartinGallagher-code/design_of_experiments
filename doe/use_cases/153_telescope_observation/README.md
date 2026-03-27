# Use Case 153: Telescope Observation Quality

## Scenario

You are observing from a suburban site with an equatorial-mount telescope and want to determine which of five equipment and setup parameters -- aperture, focal ratio, eyepiece focal length, tracking rate, and mirror cooldown time -- most strongly affect image sharpness and limiting magnitude on a given night. Testing all combinations across multiple observing sessions would take weeks of clear skies. A Plackett-Burman screening design identifies the dominant factors in just a few nights, revealing whether, for example, cooldown time matters more than aperture for suburban seeing conditions.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (sharpness, limiting_mag)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| aperture_mm | 80 | 300 | mm | Primary mirror/lens aperture |
| focal_ratio | 4 | 12 | f/ | Focal ratio |
| eyepiece_mm | 6 | 25 | mm | Eyepiece focal length |
| tracking_rate | 0.5 | 2.0 | arcsec/s | Mount tracking accuracy |
| cooldown_min | 15 | 90 | min | Thermal equilibration cooldown time |

**Fixed:** mount_type = equatorial, site = suburban

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| sharpness | maximize | pts |
| limiting_mag | maximize | mag |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 5 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template telescope_observation
cd telescope_observation
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
