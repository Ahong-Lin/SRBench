# Bench_test_8.27 — per-task scores

opus-4.8 vs haiku-4.5, 25 Harbor symbolic-regression tasks, run 2026-08-27.
Score = raw R² from each task verifier on the hidden 500-point test set
(the final 10 % of the trajectory — a time extrapolation).
`clip` = `max(-1, min(R², 1))`, the SRBench convention for aggregating.

`σ ratio` = hidden-test target σ ÷ training target σ. Below 0.05 the test
target is nearly constant, so R² divides by ~0 and the value is unstable —
those rows are marked `degen` and should not be quoted individually.

## All 25 tasks

| # | Task | opus raw | opus clip | haiku raw | haiku clip | Δ clip | Winner | σ ratio |
|--:|---|---:|---:|---:|---:|---:|:--:|---|
| 1 | `Biology_gen5_v4` | 0.8005 | +0.801 | 0.3785 | +0.378 | +0.422 | **opus** | 0.225 narrow |
| 2 | `Economy_gen5_v4` | 0.7978 | +0.798 | 0.6834 | +0.683 | +0.114 | **opus** | 0.511 ok |
| 3 | `PSEv4_m1_biology_0_004_gen5` | 0.8940 | +0.894 | -0.3764 | -0.376 | +1.270 | **opus** | 0.367 ok |
| 4 | `PSEv4_nonlinear_cubic_oscillator` | -14.7074 | -1.000 | -228417581.0769 | -1.000 | +0.000 | tie | 0.000 `degen` |
| 5 | `PSEv4_system_20260603_170953` | 1.0000 | +1.000 | 0.9890 | +0.989 | +0.011 | **opus** | 0.964 ok |
| 6 | `PSEv4_system_20260603_171349` | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.001 `degen` |
| 7 | `Physics_42_000_gen5_v4` | 0.8831 | +0.883 | 0.3868 | +0.387 | +0.496 | **opus** | 0.018 `degen` |
| 8 | `SRBench0728_Mechanics_000_gen5` | -2.6368 | -1.000 | -3.5836 | -1.000 | +0.000 | tie | 0.123 narrow |
| 9 | `SRBench0728_Mechanics_001_gen12` | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.438 ok |
| 10 | `SRBench0728_Mechanics_002_gen15` | 0.9980 | +0.998 | 0.9295 | +0.929 | +0.068 | **opus** | 0.328 ok |
| 11 | `SRBench0728_PopulationEcology_006_gen8` | 1.0000 | +1.000 | 0.0285 | +0.028 | +0.972 | **opus** | 0.981 ok |
| 12 | `SRBench0728_PopulationEcology_009_gen5` | 0.0669 | +0.067 | 0.2619 | +0.262 | -0.195 | **haiku** | 0.057 narrow |
| 13 | `SRBench0826_m2_cell_biology_and_signaling_0_000` | 0.9845 | +0.984 | -3.5045 | -1.000 | +1.984 | **opus** | 0.036 `degen` |
| 14 | `SRBench0826_m2_classical_mechanics_0_001` | 1.0000 | +1.000 | 0.6146 | +0.615 | +0.385 | **opus** | 0.009 `degen` |
| 15 | `SRBench0826_m2_classical_mechanics_0_006` | 0.8871 | +0.887 | 0.8871 | +0.887 | +0.000 | tie | 0.278 ok |
| 16 | `SRBench0826_m2_classical_mechanics_0_009` | 0.9999 | +1.000 | 0.5062 | +0.506 | +0.494 | **opus** | 0.106 narrow |
| 17 | `SRBench0826_m2_enzyme_kinetics_and_biochemistry_0_005` | 0.8742 | +0.874 | -0.1532 | -0.153 | +1.027 | **opus** | 0.045 `degen` |
| 18 | `SRBench0826_m2_epidemiology_and_disease_dynamics_0_000` | 0.9995 | +1.000 | -17.6193 | -1.000 | +2.000 | **opus** | 0.005 `degen` |
| 19 | `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | `ERR` | — | 0.0130 | +0.013 | — | — | 0.398 ok |
| 20 | `SRBench0826_m2_nuclear_and_particle_physics_0_001` | -6.3901 | -1.000 | 0.9569 | +0.957 | -1.957 | **haiku** | 0.003 `degen` |
| 21 | `SRBench0826_m2_physiology_and_homeostasis_0_004` | 0.9991 | +0.999 | 0.6779 | +0.678 | +0.321 | **opus** | 0.019 `degen` |
| 22 | `SRBench0826_m2_population_ecology_0_002` | 0.9999 | +1.000 | `ERR` | — | — | — | 1.400 ok |
| 23 | `SRBench0826_m2_population_ecology_0_004` | 0.9979 | +0.998 | 0.9964 | +0.996 | +0.001 | tie | 0.040 `degen` |
| 24 | `SRBench0826_m2_quantum_mechanics_0_003` | 1.0000 | +1.000 | -1.0000 | -1.000 | +2.000 | **opus** | 0.006 `degen` |
| 25 | `SRBench0826_m2_quantum_mechanics_0_007` | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.021 `degen` |

## Totals (23 tasks both models scored)

| Metric | opus-4.8 | haiku-4.5 |
|---|---:|---:|
| clipped mean R² | **+0.6601** | +0.2507 |
| clipped median R² | **+0.9979** | +0.5062 |
| R² ≥ 0.99 | **12 / 23** | 4 / 23 |
| R² ≥ 0.9 | **13 / 23** | 7 / 23 |
| R² ≥ 0.5 | **19 / 23** | 12 / 23 |
| R² ≥ 0.0 | **20 / 23** | 16 / 23 |
| tasks won | **14** | 2 |
| ties | 7 | 7 |
| total cost | $40.12 | **$4.07** |
| cost / scored task | $1.67 | **$0.17** |

Raw mean is deliberately omitted: haiku scored −2.28 × 10⁸ on
`PSEv4_nonlinear_cubic_oscillator`, which alone drags its raw mean to −9.5 million.

## Sorted by margin (opus − haiku, clipped)

| Task | opus | haiku | Δ |
|---|---:|---:|---:|
| `SRBench0826_m2_quantum_mechanics_0_003` | +1.000 | -1.000 | +2.000 |
| `SRBench0826_m2_epidemiology_and_disease_dynamics_0_000` | +1.000 | -1.000 | +2.000 |
| `SRBench0826_m2_cell_biology_and_signaling_0_000` | +0.984 | -1.000 | +1.984 |
| `PSEv4_m1_biology_0_004_gen5` | +0.894 | -0.376 | +1.270 |
| `SRBench0826_m2_enzyme_kinetics_and_biochemistry_0_005` | +0.874 | -0.153 | +1.027 |
| `SRBench0728_PopulationEcology_006_gen8` | +1.000 | +0.028 | +0.972 |
| `Physics_42_000_gen5_v4` | +0.883 | +0.387 | +0.496 |
| `SRBench0826_m2_classical_mechanics_0_009` | +1.000 | +0.506 | +0.494 |
| `Biology_gen5_v4` | +0.801 | +0.378 | +0.422 |
| `SRBench0826_m2_classical_mechanics_0_001` | +1.000 | +0.615 | +0.385 |
| `SRBench0826_m2_physiology_and_homeostasis_0_004` | +0.999 | +0.678 | +0.321 |
| `Economy_gen5_v4` | +0.798 | +0.683 | +0.114 |
| `SRBench0728_Mechanics_002_gen15` | +0.998 | +0.929 | +0.068 |
| `PSEv4_system_20260603_170953` | +1.000 | +0.989 | +0.011 |
| `SRBench0826_m2_population_ecology_0_004` | +0.998 | +0.996 | +0.001 |
| `PSEv4_nonlinear_cubic_oscillator` | -1.000 | -1.000 | +0.000 |
| `PSEv4_system_20260603_171349` | +1.000 | +1.000 | +0.000 |
| `SRBench0728_Mechanics_000_gen5` | -1.000 | -1.000 | +0.000 |
| `SRBench0728_Mechanics_001_gen12` | +1.000 | +1.000 | +0.000 |
| `SRBench0826_m2_classical_mechanics_0_006` | +0.887 | +0.887 | +0.000 |
| `SRBench0826_m2_quantum_mechanics_0_007` | +1.000 | +1.000 | +0.000 |
| `SRBench0728_PopulationEcology_009_gen5` | +0.067 | +0.262 | -0.195 |
| `SRBench0826_m2_nuclear_and_particle_physics_0_001` | -1.000 | +0.957 | -1.957 |

## Unscored

| Model | Task | Reason |
|---|---|---|
| opus-4.8 | `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | `NetworkConnectionError` in agent setup (2 attempts) |
| haiku-4.5 | `SRBench0826_m2_population_ecology_0_002` | `AgentSetupTimeoutError` in agent setup (2 attempts) |

Both are container-setup failures under co-tenant load, not model or task defects.

Per-task machine-readable scores: `results/scores.csv`. Full analysis: `BENCH827_REPORT.md`.
