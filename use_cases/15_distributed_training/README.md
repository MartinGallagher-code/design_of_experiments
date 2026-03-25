# Use Case 15: Distributed Deep Learning Scaling

Optimize multi-GPU distributed training for ResNet-50 on ImageNet using a Box-Behnken design.

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
