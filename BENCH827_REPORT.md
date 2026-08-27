# Bench_test_8.27: opus-4.8 vs haiku-4.5

Symbolic-regression benchmark run of 2026-08-27 over the 25 Harbor tasks in
`Bench_test_8.27`. Both models solve each task from scratch inside
a container (write `/app/law.py` + `/app/explain.md`); the verifier scores raw R²
on a hidden test set the agent never sees.

## 1. Headline

Comparing the **23 tasks both models scored** (each model lost one different task
to an infrastructure error — see §6):

| Metric | opus-4.8 | haiku-4.5 |
|---|---|---|
| clipped mean R² | **+0.660** | +0.251 |
| clipped median R² | **+0.998** | +0.506 |
| R² ≥ 0.99 | **12 / 23** (52 %) | 4 / 23 (17 %) |
| R² ≥ 0.9 | **13 / 23** (57 %) | 7 / 23 (30 %) |
| R² ≥ 0.5 | **19 / 23** (83 %) | 12 / 23 (52 %) |
| R² ≥ 0.0 | **20 / 23** (87 %) | 16 / 23 (70 %) |
| head-to-head | **wins 14** | wins 2, ties 7 |
| total cost | $40.12 | **$4.07** |
| cost / task | $1.67 | **$0.17** |
| agent wall-clock | 203 min | **67 min** |
| output tokens | 721 k | **271 k** |

opus-4.8 costs **9.9×** more and buys **+0.41** clipped mean R² and 3× as many
near-perfect solves. Whether that trade is worth it depends on how much a
near-exact law matters versus an approximate one.

**Read clipped R², not raw.** haiku scored **−2.28 × 10⁸** on
`PSEv4_nonlinear_cubic_oscillator`, which alone drags its raw mean to −9.5
million. Every aggregate here uses `clipped = max(−1, min(R², 1))`, the SRBench
convention.

## 2. Per-task scores

`Δclip` = opus − haiku (positive = opus better). `test/train σ` is the hidden-test
target standard deviation divided by the training one — see §4, it decides whether
a score is meaningful.

| Task | Set | opus raw | opus clip | haiku raw | haiku clip | Δclip | Win | test/train σ |
|---|---|---:|---:|---:|---:|---:|:-:|---|
| `Biology_gen5_v4` | gen5v4 | 0.8005 | +0.801 | 0.3785 | +0.378 | +0.422 | **O** | 0.225 narrow |
| `Economy_gen5_v4` | gen5v4 | 0.7978 | +0.798 | 0.6834 | +0.683 | +0.114 | **O** | 0.511 ok |
| `PSEv4_m1_biology_0_004_gen5` | PSEv4 | 0.8940 | +0.894 | -0.3764 | -0.376 | +1.270 | **O** | 0.367 ok |
| `PSEv4_nonlinear_cubic_oscillator` | PSEv4 | -14.7074 | -1.000 | -228417581.0769 | -1.000 | +0.000 | tie | 0.000 **degen** |
| `PSEv4_system_20260603_170953` | PSEv4 | 1.0000 | +1.000 | 0.9890 | +0.989 | +0.011 | **O** | 0.964 ok |
| `PSEv4_system_20260603_171349` | PSEv4 | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.001 **degen** |
| `Physics_42_000_gen5_v4` | gen5v4 | 0.8831 | +0.883 | 0.3868 | +0.387 | +0.496 | **O** | 0.018 **degen** |
| `SRBench0728_Mechanics_000_gen5` | 0728 | -2.6368 | -1.000 | -3.5836 | -1.000 | +0.000 | tie | 0.123 narrow |
| `SRBench0728_Mechanics_001_gen12` | 0728 | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.438 ok |
| `SRBench0728_Mechanics_002_gen15` | 0728 | 0.9980 | +0.998 | 0.9295 | +0.929 | +0.068 | **O** | 0.328 ok |
| `SRBench0728_PopulationEcology_006_gen8` | 0728 | 1.0000 | +1.000 | 0.0285 | +0.028 | +0.972 | **O** | 0.981 ok |
| `SRBench0728_PopulationEcology_009_gen5` | 0728 | 0.0669 | +0.067 | 0.2619 | +0.262 | -0.195 | **H** | 0.057 narrow |
| `SRBench0826_m2_cell_biology_and_signaling_0_000` | 0826 | 0.9845 | +0.984 | -3.5045 | -1.000 | +1.984 | **O** | 0.036 **degen** |
| `SRBench0826_m2_classical_mechanics_0_001` | 0826 | 1.0000 | +1.000 | 0.6146 | +0.615 | +0.385 | **O** | 0.009 **degen** |
| `SRBench0826_m2_classical_mechanics_0_006` | 0826 | 0.8871 | +0.887 | 0.8871 | +0.887 | +0.000 | tie | 0.278 ok |
| `SRBench0826_m2_classical_mechanics_0_009` | 0826 | 0.9999 | +1.000 | 0.5062 | +0.506 | +0.494 | **O** | 0.106 narrow |
| `SRBench0826_m2_enzyme_kinetics_and_biochemistry_0_005` | 0826 | 0.8742 | +0.874 | -0.1532 | -0.153 | +1.027 | **O** | 0.045 **degen** |
| `SRBench0826_m2_epidemiology_and_disease_dynamics_0_000` | 0826 | 0.9995 | +1.000 | -17.6193 | -1.000 | +2.000 | **O** | 0.005 **degen** |
| `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | 0826 | ERR | — | 0.0130 | +0.013 | — | — | 0.398 ok |
| `SRBench0826_m2_nuclear_and_particle_physics_0_001` | 0826 | -6.3901 | -1.000 | 0.9569 | +0.957 | -1.957 | **H** | 0.003 **degen** |
| `SRBench0826_m2_physiology_and_homeostasis_0_004` | 0826 | 0.9991 | +0.999 | 0.6779 | +0.678 | +0.321 | **O** | 0.019 **degen** |
| `SRBench0826_m2_population_ecology_0_002` | 0826 | 0.9999 | +1.000 | ERR | — | — | — | 1.400 ok |
| `SRBench0826_m2_population_ecology_0_004` | 0826 | 0.9979 | +0.998 | 0.9964 | +0.996 | +0.001 | tie | 0.040 **degen** |
| `SRBench0826_m2_quantum_mechanics_0_003` | 0826 | 1.0000 | +1.000 | -1.0000 | -1.000 | +2.000 | **O** | 0.006 **degen** |
| `SRBench0826_m2_quantum_mechanics_0_007` | 0826 | 1.0000 | +1.000 | 1.0000 | +1.000 | +0.000 | tie | 0.021 **degen** |

## 3. Where the difference comes from

**By task family** (clipped mean, intersection only):

| Task set | n | opus | haiku | Δ |
|---|---:|---:|---:|---:|
| `SRBench0826_*` (the v6 candidates generated 2026-08-26) | 11 | **+0.795** | +0.226 | +0.569 |
| `gen5_v4` | 3 | **+0.827** | +0.483 | +0.344 |
| `PSEv4_*` | 4 | **+0.473** | +0.153 | +0.320 |
| `SRBench0728_*` | 5 | **+0.413** | +0.244 | +0.169 |

The freshly generated `SRBench0826` set separates the two models most sharply
(Δ +0.57), which is the useful property for a benchmark.

**Discrimination.** Of the 23 shared tasks, 7 are ties: 4 where both models score
≈1.0 (too easy) and 2 where both are ≤ −1 (too hard), plus one exact tie at 0.887.
That leaves **16 genuinely discriminating tasks, and opus wins 14 of them.** This
is a large improvement over the 2026-08-06 set, where only 1 of 6 tasks
discriminated at all — the cause is the split (§4).

**The 2 tasks haiku won:**

- `SRBench0826_m2_nuclear_and_particle_physics_0_001` — haiku **+0.957** vs opus
  **−6.39**. This is a real and instructive opus failure. Reading both `law.py`
  files: opus derived the analytic Bateman solution and returned a **closed form
  in `t` alone**, discarding the observed `Np`/`Nd` state columns, so its fitted
  decay constants drift once `t` leaves the training window. haiku kept the
  **state-feedback form** `λ_p·Np − λ_d·Nd + A·exp(−k·t)`, which stays anchored by
  the observed states and therefore extrapolates. Being "more physical" hurt here.
- `SRBench0728_PopulationEcology_009_gen5` — haiku +0.262 vs opus +0.067. Both
  effectively failed; neither found the law. Not a meaningful haiku win.

## 4. Methodological caveat: 12 hidden test sets have collapsed variance

All 25 tasks split 4500 train / 500 test as a **time extrapolation** — the test set
is the final 10 % of the trajectory. That is why this benchmark discriminates far
better than an i.i.d. holdout. But it has a side effect that must be reported:

Most tasks are ODE systems that **settle toward equilibrium**, so the last 10 % of
time is the flat tail. R² divides by the test target's variance, and in 12 of 25
tasks that variance has nearly vanished (ratio < 0.05, down to 0.000):

| Stratum (test σ / train σ) | n | opus | haiku | Δ | opus wins | haiku wins |
|---|---:|---:|---:|---:|---:|---:|
| healthy ≥ 0.25 | 7 | **+0.940** | +0.592 | +0.348 | 5 | 0 |
| narrow 0.05–0.25 | 4 | **+0.217** | +0.037 | +0.180 | 2 | 1 |
| degenerate < 0.05 | 12 | **+0.645** | +0.123 | +0.522 | 7 | 1 |

In the degenerate stratum R² is hypersensitive: a tiny absolute error becomes a
huge negative R², which is exactly how haiku reached −2.28 × 10⁸ and −17.6. Those
scores say more about the metric than the model.

**The ranking survives stratification** — opus leads in all three strata and wins
5–0 among the 7 healthiest tasks — so the conclusion is robust. But the *magnitude*
in the degenerate stratum is not trustworthy, and per-task scores there should not
be quoted individually. The 7 healthy tasks are the defensible subset:

| Task | opus | haiku | Δ |
|---|---:|---:|---:|
| `PSEv4_m1_biology_0_004_gen5` | +0.894 | −0.376 | +1.270 |
| `SRBench0728_PopulationEcology_006_gen8` | +1.000 | +0.028 | +0.972 |
| `Economy_gen5_v4` | +0.798 | +0.683 | +0.114 |
| `SRBench0728_Mechanics_002_gen15` | +0.998 | +0.929 | +0.068 |
| `PSEv4_system_20260603_170953` | +1.000 | +0.989 | +0.011 |
| `SRBench0728_Mechanics_001_gen12` | +1.000 | +1.000 | 0.000 |
| `SRBench0826_m2_classical_mechanics_0_006` | +0.887 | +0.887 | 0.000 |

Fixing this means choosing the test window by target dynamics rather than by a
fixed 90 % time cut, or scoring with an absolute-error metric (NMSE against
training variance) instead of test-set-normalised R².

## 5. Cost and effort per task

| Task | opus $ | haiku $ | opus min | haiku min | opus out-tok | haiku out-tok |
|---|---:|---:|---:|---:|---:|---:|
| `Biology_gen5_v4` | 1.41 | 0.32 | 6.2 | 6.0 | 23,185 | 24,694 |
| `Economy_gen5_v4` | 2.18 | 0.25 | 14.7 | 4.8 | 41,690 | 18,480 |
| `PSEv4_m1_biology_0_004_gen5` | 1.85 | 0.20 | 9.2 | 1.9 | 33,401 | 7,300 |
| `PSEv4_nonlinear_cubic_oscillator` | 0.97 | 0.10 | 4.8 | 1.7 | 17,522 | 6,556 |
| `PSEv4_system_20260603_170953` | 0.16 | 0.41 | 0.7 | 4.0 | 1,541 | 19,775 |
| `PSEv4_system_20260603_171349` | 0.14 | 0.11 | 0.5 | 0.9 | 1,787 | 2,555 |
| `Physics_42_000_gen5_v4` | 0.70 | 0.28 | 3.8 | 2.7 | 12,314 | 11,969 |
| `SRBench0728_Mechanics_000_gen5` | 5.44 | 0.20 | 27.4 | 4.3 | 93,661 | 17,685 |
| `SRBench0728_Mechanics_001_gen12` | 0.17 | 0.10 | 0.7 | 1.7 | 1,896 | 6,285 |
| `SRBench0728_Mechanics_002_gen15` | 2.24 | 0.20 | 10.7 | 5.4 | 40,846 | 13,978 |
| `SRBench0728_PopulationEcology_006_gen8` | 1.23 | 0.12 | 6.6 | 2.3 | 23,968 | 9,099 |
| `SRBench0728_PopulationEcology_009_gen5` | 3.29 | 0.20 | 15.5 | 3.2 | 56,664 | 17,854 |
| `SRBench0826_m2_cell_biology_and_signaling_0_000` | 1.36 | 0.14 | 7.0 | 2.3 | 24,687 | 11,088 |
| `SRBench0826_m2_classical_mechanics_0_001` | 2.12 | 0.11 | 11.1 | 1.9 | 40,748 | 9,202 |
| `SRBench0826_m2_classical_mechanics_0_006` | 0.66 | 0.10 | 3.4 | 1.5 | 11,599 | 7,035 |
| `SRBench0826_m2_classical_mechanics_0_009` | 2.29 | 0.19 | 10.1 | 3.0 | 35,242 | 17,498 |
| `SRBench0826_m2_enzyme_kinetics_and_biochemistry_0_005` | 2.05 | 0.15 | 10.0 | 2.0 | 38,475 | 8,381 |
| `SRBench0826_m2_epidemiology_and_disease_dynamics_0_000` | 4.72 | 0.12 | 24.4 | 2.0 | 86,743 | 9,345 |
| `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | 0.00 | 0.19 | 0.0 | 3.3 | 0 | 4,337 |
| `SRBench0826_m2_nuclear_and_particle_physics_0_001` | 1.89 | 0.10 | 9.9 | 1.7 | 39,977 | 8,700 |
| `SRBench0826_m2_physiology_and_homeostasis_0_004` | 2.38 | 0.14 | 12.3 | 4.6 | 43,506 | 12,184 |
| `SRBench0826_m2_population_ecology_0_002` | 0.64 | 0.00 | 3.1 | 0.0 | 10,820 | 0 |
| `SRBench0826_m2_population_ecology_0_004` | 1.20 | 0.09 | 6.3 | 1.6 | 24,360 | 8,063 |
| `SRBench0826_m2_quantum_mechanics_0_003` | 0.40 | 0.12 | 1.8 | 1.9 | 6,151 | 9,289 |
| `SRBench0826_m2_quantum_mechanics_0_007` | 0.63 | 0.13 | 3.0 | 1.9 | 10,616 | 9,839 |

opus spends its budget very unevenly: `SRBench0728_Mechanics_000_gen5` cost $5.44
and 27 min and still scored −2.64, while `PSEv4_system_20260603_171349` cost $0.14
and scored 1.000. High spend correlates with hard tasks, not with success.

## 6. Errors and reproduction

Each model lost exactly one task to infrastructure, both under heavy load from a
co-tenant `learn2design` job that pushed the box to load 96–130 and left ~3 GB RAM:

| Model | Task | Error | Attempts |
|---|---|---|---|
| opus-4.8 | `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | `NetworkConnectionError` | 2 |
| haiku-4.5 | `SRBench0826_m2_population_ecology_0_002` | `AgentSetupTimeoutError` | 2 |

Both are harbor agent-setup failures (`npm install -g @anthropic-ai/claude-code`
timing out in-container), not model or task defects. A first retry round recovered
one opus task — `SRBench0826_m2_classical_mechanics_0_009` scored **0.9999** — so
filling gaps has so far only widened opus's lead. The remaining two are worth
re-running when the machine is quiet; they will not change the ranking.

### Configuration

| | opus-4.8 | haiku-4.5 |
|---|---|---|
| model id | `claude-opus-4-8` | `claude-haiku-4-5` |
| proxy | Bedrock passthrough, port 8788 | port 8789 |
| reasoning effort | `high` | none (no extended thinking; its gateway 400s on `output_config.effort`) |
| concurrency | 5 | 5 |
| attempts per task | 1 | 1 |
| agent | `claude-code` 2.1.247 | same |
| per-task limits | 1 CPU, 2048 MB, 3600 s agent timeout, 600 s verifier | same |

### Artifacts

This branch carries the final output of every trial, extracted from the harbor
job directories:

```
results/
  scores.csv                     per-task raw + clipped R² and cost, both models
  opus-4.8/<task>/
    law.py                       the submitted law, exactly as scored
    explain.md                   the model's own writeup
    reward.txt                   raw test R²
    verifier_stdout.txt          verifier output (NMSE / NMAE / R²)
    trial_meta.json              cost, tokens, timestamps, source job
  haiku-4.5/<task>/              same
```

The full harbor jobs — agent trajectories, CLI session state and per-trial logs
— stay on the machine that ran them, under `outputs/harbor_jobs/`:

```
bench827_opus48/         23 scored trials, result.json          15 MB
bench827_haiku45/        24 scored trials, result.json          16 MB
bench827_opus48_retry/   1 recovered (classical_mechanics_0_009) 856 KB
bench827_haiku45_retry/  retry failed again                      80 KB
```

There, each trial directory holds the agent trajectory plus the submitted
`law.py` and `explain.md` inside `verifier/test-stdout.txt`. Re-summarise a job
with `harbor_run/summarize.py <job_dir>`, or re-extract this tree with
`harbor_run/extract_bench827_outputs.py <jobs_dir> results`.

Re-run the benchmark with `harbor_run/run_srbench_harbor.sh`, pointing
`TASKS_DIR` at the 25 task definitions and selecting the model:

```bash
TASKS_DIR=<tasks> JOB_NAME=bench827_opus48 \
  PRESET=opus-4.8 PROXY_PORT=8788 MODEL=claude-opus-4-8 \
  N_CONCURRENT=5 ./run_srbench_harbor.sh

TASKS_DIR=<tasks> JOB_NAME=bench827_haiku45 \
  PRESET=haiku-4.5 PROXY_PORT=8789 MODEL=claude-haiku-4-5 \
  N_CONCURRENT=5 ./run_srbench_harbor.sh
```

The runner and proxy scripts are deliberately not committed here: they hardcode
internal gateway hostnames.

## 7. Takeaways

1. **opus-4.8 clearly outperforms haiku-4.5** on symbolic-regression extrapolation:
   clipped mean +0.660 vs +0.251, median 0.998 vs 0.506, 14–2 head-to-head. The
   ranking holds in every variance stratum.
2. **It costs ~10× more.** $1.67 vs $0.17 per task. haiku still clears R² ≥ 0.5 on
   half the tasks, so it remains reasonable when an approximate law suffices.
3. **The time-extrapolation split is the right call** — 16 of 23 tasks discriminate,
   versus 1 of 6 on the old i.i.d. gate.
4. **But 12 of 25 test sets have degenerate target variance** and need re-splitting
   or a different metric before per-task numbers there are quotable.
5. **opus has a characteristic failure mode worth studying**: on the decay-chain
   task it substituted an analytic closed form in `t` for the state-feedback form
   and lost the extrapolation, scoring −6.39 where haiku scored +0.957. Deriving
   the "correct physics" is not always the same as fitting a law that extrapolates.
