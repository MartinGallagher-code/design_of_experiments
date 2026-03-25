# Use Case 3: ML Hyperparameter Screening

## Scenario

You are training a deep learning model and need to screen 5 hyperparameters to find which ones matter most. Running a full factorial (2^5 = 32 runs) is too expensive — each training run takes significant GPU time. A fractional factorial gives you the key insights in fewer runs.

**This use case demonstrates:**
- Fractional factorial design (Resolution III, fewer runs than full factorial)
- Mixed factor types (continuous + categorical)
- `positional` argument style (factors passed as ordered positional args)
- `--seed` for reproducible run order
- Multi-response with mixed optimization directions (maximize accuracy, minimize training time)
- Shell-format runner script (default `--format sh`)

## Factors

| Factor | Low | High | Type | Description |
|--------|-----|------|------|-------------|
| learning_rate | 0.001 | 0.1 | continuous | SGD learning rate |
| batch_size | 32 | 256 | continuous | Training batch size |
| dropout | 0.1 | 0.5 | continuous | Dropout probability |
| hidden_layers | 2 | 6 | continuous | Number of hidden layers |
| optimizer | sgd | adam | categorical | Optimization algorithm |

**Fixed:** epochs = 50, dataset = cifar10

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| accuracy | maximize | % |
| training_time | minimize | sec |

## Why Fractional Factorial?

- With 5 factors at 2 levels, full factorial = 32 runs
- Fractional factorial (Resolution III) uses only 8-16 runs
- We're *screening* — we just need to know which factors have the largest effects
- Some main effects are confounded with 2-factor interactions (the trade-off for fewer runs)
- Follow-up experiments can focus on the important factors

## Running the Demo

### Prerequisites

```bash
cd /workspaces/design_of_experiments
pip install -r requirements.txt
```

### Step 1: Preview the design

```bash
python doe.py info --config use_cases/03_ml_hyperparameter_screening/config.json
```

Output:
```
Plan      : ML Hyperparameter Screening
Operation : fractional_factorial
Factors   : learning_rate, batch_size, dropout, hidden_layers, optimizer
Base runs : 16
Blocks    : 1
Total runs: 16
Responses : accuracy [maximize] (%), training_time [minimize] (sec)
Fixed     : epochs=50, dataset=cifar10
```

Notice the run count is 16 instead of 32 — the fractional factorial has halved the experiment.

### Step 2: Generate the runner script with a seed

```bash
python doe.py generate --config use_cases/03_ml_hyperparameter_screening/config.json \
    --output use_cases/03_ml_hyperparameter_screening/results/run.sh --seed 7
```

Open `use_cases/03_ml_hyperparameter_screening/results/run.sh` to see how `positional` argument style passes factors as ordered values (no `--flag` names) to the test script.

### Step 3: Execute the experiments

```bash
bash use_cases/03_ml_hyperparameter_screening/results/run.sh
```

Each simulated training run produces accuracy and training_time results.

### Step 4: Analyze results

```bash
python doe.py analyze --config use_cases/03_ml_hyperparameter_screening/config.json
```

The analysis shows main effects for both responses:
- **accuracy**: Which hyperparameters have the biggest impact on test accuracy?
- **training_time**: Which hyperparameters drive training time?

Look for factors that matter for accuracy but don't hurt training time — those are the "free wins."

### Step 5: Optimize for a specific response

```bash
python doe.py optimize --config use_cases/03_ml_hyperparameter_screening/config.json
```

Reports best observed settings and factor importance for both accuracy and training time.

### Step 6: Generate the report

```bash
python doe.py report --config use_cases/03_ml_hyperparameter_screening/config.json \
    --output use_cases/03_ml_hyperparameter_screening/results/report.html
```

## Features Exercised

| Feature | Value |
|---------|-------|
| Design type | `fractional_factorial` |
| Factor types | `continuous` (4) + `categorical` (1) |
| Arg style | `positional` |
| Script format | `sh` (default) |
| `--seed` | 7 |
| Fixed factors | epochs, dataset |
| Multi-response | accuracy (maximize), training_time (minimize) |
| Run reduction | 16 runs instead of 32 |

## Files

- Config: `use_cases/03_ml_hyperparameter_screening/config.json`
- Simulator: `use_cases/03_ml_hyperparameter_screening/sim.sh`
- Results: `use_cases/03_ml_hyperparameter_screening/results/`
- Report: `use_cases/03_ml_hyperparameter_screening/results/report.html`
