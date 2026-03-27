# Use Case 15: Distributed Deep Learning Scaling

## Scenario

You are optimizing multi-GPU distributed training of ResNet-50 on ImageNet, balancing raw throughput against scaling efficiency. Adding more GPUs increases images processed per second but suffers diminishing returns from gradient synchronization overhead, and larger per-GPU batches boost throughput at the risk of degrading convergence. A Box-Behnken design efficiently explores the three-factor space at three levels while avoiding extreme corner combinations.

**This use case demonstrates:**
- Box-Behnken design for three-factor response surface modeling
- Sublinear GPU scaling and gradient compression trade-offs
- Balancing training throughput against scaling efficiency

## Factors

| Factor                | Low | High | Unit   |
|-----------------------|-----|------|--------|
| gpu_count             | 8   | 64   | GPUs   |
| batch_per_gpu         | 32  | 256  | images |
| gradient_compression  | 0   | 90   | %      |

**Fixed:** model=resnet50, dataset=imagenet

## Responses

- **images_per_sec** (maximize, img/s) -- scales sublinearly with GPU count, boosted by larger batch
- **scaling_efficiency** (maximize, %) -- drops with more GPUs, helped by gradient compression

## Running

```bash
doe run config.json
# or manually:
bash sim.sh --gpu_count 32 --batch_per_gpu 128 --gradient_compression 50 --out result.json
```
