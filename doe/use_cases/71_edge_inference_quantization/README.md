# Use Case 71: Edge Inference Quantization

## Scenario

You are deploying a MobileNetV2 model via TensorFlow Lite on an edge device and need to minimize inference latency without unacceptable accuracy degradation from quantization. There are 6 parameters to investigate -- weight bit width, activation bit width, batch size, worker threads, model cache, and memory pool -- and profiling each configuration on-device is slow. A Plackett-Burman screening design identifies which quantization and runtime settings dominate the latency-accuracy trade-off in just 8 runs.

**This use case demonstrates:**
- Plackett-Burman design
- Multi-response analysis (inference_latency_ms, accuracy_loss_pct)
- Interactive HTML report generation

## Factors

| Factor | Low | High | Unit | Description |
|--------|-----|------|------|-------------|
| weight_bits | 4 | 16 | bits | Weight quantization bit width |
| activation_bits | 4 | 16 | bits | Activation quantization bit width |
| batch_size | 1 | 32 | samples | Inference batch size |
| num_threads | 1 | 4 | threads | Inference worker threads |
| cache_size_kb | 64 | 512 | KB | Model cache size |
| memory_pool_mb | 16 | 128 | MB | Runtime memory pool |

**Fixed:** framework = tflite, model = mobilenet_v2

## Responses

| Response | Direction | Unit |
|----------|-----------|------|
| inference_latency_ms | minimize | ms |
| accuracy_loss_pct | minimize | % |

## Why Plackett-Burman?

- A highly efficient screening design requiring only N+1 runs for N factors
- Focuses on estimating main effects, making it perfect for an initial screening stage
- Best when the goal is to quickly separate important factors from trivial ones
- We have 6 factors in this experiment

## Running the Demo

### Step 1: Initialize the experiment
```bash
doe init --template edge_inference_quantization
cd edge_inference_quantization
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
