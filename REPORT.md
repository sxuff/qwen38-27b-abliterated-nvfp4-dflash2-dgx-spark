# Measured comparison

**Frozen qualification verdict: NO-GO.**

- no-spec median end-to-end completion rate: **12.33 tok/s**
- DFlash2 median end-to-end completion rate: **41.44 tok/s**
- aggregate median ratio: **3.36x**
- median paired row ratio: **3.36x**
- exact outputs: **16/27**
- quality: **23/27 no-spec**, **23/27 DFlash2**
- operational completion: **True**
- safety eligible: **True**
- DFlash activation: **True**
- frozen quality gate complete: **False**
- minimum MemAvailable: **27.67 GiB no-spec**, **27.54 GiB DFlash2**
- maximum swap growth: **0 bytes no-spec**, **0 bytes DFlash2**
- DFlash2 final acceptance: **5.95 tokens**, **0.7071428571428572 rate**, **1156.0 verification calls**

## Per-fixture median end-to-end completion tok/s

| Fixture | No spec | DFlash2 | Ratio |
|---|---:|---:|---:|
| code | 12.37 | 50.15 | 4.05x |
| copy_json | 12.36 | 70.58 | 5.71x |
| copy_python | 12.36 | 68.85 | 5.57x |
| json | 11.71 | 30.29 | 2.59x |
| literal | 7.95 | 9.22 | 1.16x |
| math | 12.37 | 41.37 | 3.35x |
| prose | 12.27 | 22.69 | 1.85x |
| reasoning | 12.27 | 49.41 | 4.03x |
| tool | 11.87 | 39.92 | 3.36x |

The frozen quality gate remained failed for the same fixtures in both arms: copy_json (2/3 passes in each arm), prose (0/3 passes in each arm). Shared failures remain failures; post-hoc inspection does not relabel them.

One paired three-repetition operational sweep on one NVIDIA GB10. Results are workload-specific. Exact parity and quality are separate outcomes. The fixed no-spec then DFlash2 order does not isolate run-order drift.
