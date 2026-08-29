# Target artifact

This recipe pins `aday777/Qwen3.8-27B-ARA-abliterated-NVFP4-MTP` at `16b43988bddfbe3ae0fd172c02c4ad9099c678de`.

## Why this target

The target was already present and fully hash-verified on the test GX10. Its artifact package includes a build manifest, a runtime validation report, and SHA-256 values for every selected file. Using it avoids substituting a different abliteration method during a decoding-runtime experiment.

The 20.58 GB package contains:

- compressed-tensors NVFP4 W4A4 language-model linear layers
- BF16 `lm_head`
- BF16 recurrent convolution paths
- 333 BF16 vision tensors reported bit-exact against the source
- 15 BF16 MTP tensors reported bit-exact against the source

The source build manifest labels the abliteration method as Heretic 1.2.0 plus custom arbitrary-rank ablation. It reports 0/100 refusals and KL divergence `0.05345083400607109`. Those are source-artifact claims, not results re-measured by this repository.

The source validation report passed text, a math control, a benign refusal-surface probe, vision OCR, native MTP acceptance, and post-runtime integrity on an RTX PRO 6000 Blackwell system. This repository separately tests the artifact on one GB10 under the pinned SGLang runtime.

## Why no replacement quant was downloaded

A newer Huihui-based NVFP4 artifact exists, but it represents a different abliteration and did not have matched evidence proving it superior for this deployment. Downloading another roughly 20.59 GB target would also have reduced the live GX10's remaining disk reserve from approximately 31 GB to approximately 10 GB. The existing validated target was therefore the stronger fit-safe choice for this isolated runtime treatment.

Exact selected files, sizes, and hashes are in [`../manifests/target.json`](../manifests/target.json).
