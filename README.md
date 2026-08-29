# Qwen3.8-27B ARA abliterated NVFP4 + DFlash2 on one DGX Spark

A pinned SGLang recipe for serving `aday777/Qwen3.8-27B-ARA-abliterated-NVFP4-MTP` with DFlash2 speculative decoding on one NVIDIA GB10 system.

## Exact stack

- Target: `aday777/Qwen3.8-27B-ARA-abliterated-NVFP4-MTP` at `16b43988bddfbe3ae0fd172c02c4ad9099c678de`
- Draft: `z-lab/Qwen3.8-27B-DFlash2` at `50307d4c4cde6860d4eee73e2547cd786fe8e8a4`
- Base image: `lmsysorg/sglang@sha256:febfb971c7352570fc445c466ebd6ffc9d896024958e544a60f2137fd85856b1`
- Hardware: one NVIDIA DGX Spark or equivalent GB10 with 128 GB unified memory
- Target format: compressed-tensors NVFP4 W4A4 with BF16 `lm_head`, vision, recurrent convolutions, and native MTP tensors

Exact artifact sizes and SHA-256 values are in [`manifests`](manifests).

## Build

```bash
./scripts/build_image.sh
```

## Serve

```bash
MODEL_DIR=/path/to/target/snapshot \
DRAFT_DIR=/path/to/draft/snapshot \
./scripts/serve.sh
```

Use the no-spec control or fallback explicitly:

```bash
MODE=no-spec \
MODEL_DIR=/path/to/target/snapshot \
./scripts/serve.sh
```

The endpoint binds to localhost by default at `http://127.0.0.1:8001/v1`.

## Benchmark

The frozen study uses the same target, runtime, prompts, sampler, and launch settings in both arms. The treatment adds only DFlash2 and its pinned draft.

```bash
MODEL_DIR=/path/to/target/snapshot \
DRAFT_DIR=/path/to/draft/snapshot \
./scripts/run_study.sh
```

See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) and [`protocol.json`](protocol.json) for the exact contract.

## Scope

This recipe does not claim that abliteration is lossless, that DFlash2 preserves exact output tokens, or that one workload predicts universal throughput. Speed, acceptance, exact output parity, executable or semantic quality, and memory safety are measured separately.

## Attribution

- [MiaAI-Lab/Qwen3.8-27B-SGLang-DGX-Spark](https://github.com/MiaAI-Lab/Qwen3.8-27B-SGLang-DGX-Spark) established the GB10 serving scaffold and compatibility-overlay lineage used here.
- SGLang provides the serving runtime and DFlash2 integration.
- z-lab and Inco AI provide the DFlash2 draft.
- Aday provides the validated ARA-abliterated NVFP4 target.

## Licenses

Repository scripts are MIT licensed. Copied SGLang modules retain their Apache-2.0 headers and license. Model artifacts are not included and retain their upstream licenses.
