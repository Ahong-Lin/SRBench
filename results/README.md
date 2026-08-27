# Bench_test_8.27 results — opus-4.8 vs haiku-4.5

Final output of every trial from the 2026-08-27 symbolic-regression benchmark
run over the 25 Harbor tasks in `Bench_test_8.27`.

Each model ran as a `claude-code` agent inside a container: it saw only
`/app/data/train_data.csv` (4,500 points) and had to write `/app/law.py` and
`/app/explain.md`. The verifier then scored raw R² on a hidden 500-point test
set — **the final 10 % of the trajectory, so this measures time extrapolation,
not interpolation.**

## Headline

23 tasks were scored by both models (each lost one different task to an
infrastructure error):

| Metric | opus-4.8 | haiku-4.5 |
|---|---:|---:|
| clipped mean R² | **+0.660** | +0.251 |
| clipped median R² | **+0.998** | +0.506 |
| R² ≥ 0.99 | **12 / 23** | 4 / 23 |
| R² ≥ 0.5 | **19 / 23** | 12 / 23 |
| tasks won | **14** | 2 (7 ties) |
| cost | $40.12 ($1.67/task) | **$4.07 ($0.17/task)** |

opus-4.8 costs ~10× more for +0.41 clipped mean R² and 3× as many near-perfect
solves.

## Layout

```
results/
  scores.csv            per-task raw + clipped R², cost and status, both models
  opus-4.8/<task>/
    law.py              the submitted law, exactly as scored
    explain.md          the model's own writeup
    reward.txt          raw test R²
    verifier_stdout.txt verifier output (NMSE / NMAE / R²)
    trial_meta.json     cost, tokens, timestamps, source job
  haiku-4.5/<task>/     same
BENCH827_SCORES.md      per-task score tables
BENCH827_REPORT.md      full analysis: cost, failure modes, caveats
```

All 48 `law.py` files parse; each is standalone and re-runnable against the
matching task's `tests/test_data.csv`.

## Two caveats before quoting a number

**Use clipped R², not raw.** haiku scored −2.28 × 10⁸ on
`PSEv4_nonlinear_cubic_oscillator`, which alone drags its raw mean to −9.5
million. Aggregates use `clipped = max(-1, min(R², 1))`.

**12 of 25 hidden test sets have collapsed target variance.** Most tasks are ODE
systems settling toward equilibrium, and the test window is the flat tail, so R²
divides by a near-zero variance and becomes unstable. `BENCH827_SCORES.md` marks
these rows `degen`; do not quote them individually. The ranking survives
stratification — opus leads in all three variance strata and wins 5–0 among the
7 healthiest tasks — but the magnitudes in the degenerate stratum are not
trustworthy.

## Unscored

| Model | Task | Reason |
|---|---|---|
| opus-4.8 | `SRBench0826_m2_epidemiology_and_disease_dynamics_0_005` | `NetworkConnectionError` |
| haiku-4.5 | `SRBench0826_m2_population_ecology_0_002` | `AgentSetupTimeoutError` |

Both are container agent-setup failures (`npm install` timing out) under
co-tenant load on the host, not model or task defects. Each was retried once and
failed the same way. A separate retry did recover
`SRBench0826_m2_classical_mechanics_0_009` for opus at R² = 0.9999.

## Provenance

The 12 `SRBench0826_*` tasks are drawn from the 137 v6 candidates generated on
2026-08-26 (branch `candidates/v6-147-20260826`). They discriminate between the
two models most sharply of any subset here (Δ +0.57 clipped mean).
