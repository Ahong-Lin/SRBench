# Bench_test_8.28 — opus-4.8 vs haiku-4.5 (25 tasks × 3 attempts each)

Run date: 2026-08-29/30. Source: `Bench_test_8.28.zip`.
Runner: `harbor_run/run_srbench_harbor.sh` (local Docker, one container per trial,
hyra Anthropic-compat proxy → internal gateway), `-k 3 -n 4`.

**150 trials, 150 scored.** opus-4.8 75/75 with zero exceptions; haiku-4.5 74/75
plus one retry (a transient `NetworkConnectionError` — TLS failure while installing
the `claude` CLI, infrastructure not model) for 75/75.

Jobs: `outputs/harbor_jobs/b828_{opus48,haiku45,haiku45_retry}` (gitignored).
Artefacts + scores: `harbor_run/b828_outputs/` (committed) — all 150 `law.py` and
150 `explain.md`.

---

## 1. Headline

| | opus-4.8 | haiku-4.5 |
|---|---|---|
| trials scored | 75 / 75 | 75 / 75 (1 retry) |
| **head-to-head (per-task median clipped R²)** | **24 wins** | **0 wins** (1 tie) |
| macro-mean of per-task median clipped R² | **0.866** | 0.170 |
| median of per-task medians | **0.9999** | 0.595 |
| tasks with median clipped R² ≥ 0.9 | **21 / 25** | 10 / 25 |
| tasks with median clipped R² ≤ 0 | **1 / 25** | 10 / 25 |
| median spread across 3 attempts | **0.0013** | 0.268 |
| laws using an sklearn regressor | **0** | 2 |
| total cost | $200.24 | $13.90 |
| median cost / trial | $2.47 | $0.16 |

**opus wins 24 of 25 tasks and loses none.** This is the opposite situation from
the `ai_scaling_u_shape` task run yesterday, where every model scored ≈1.0 and the
metric could not discriminate. This set genuinely discriminates, and the reason is
structural: **24 of the 25 holdouts are extrapolation segments** (see §2), where
memorizing the training curve earns nothing.

The single "tie" is an artifact of clipping — see §4.

---

## 2. Task audit first (`harbor_run/audit_b828_tasks.py`)

Before reading any score I audited all 25 tasks against their own verifier
contract (`FEATURE_NAMES`/`TARGET_NAME` parsed from `tests/test_outputs.py`).
Full output: `harbor_run/b828_task_audit.json`.

- **24 / 25 holdouts are extrapolation**, 1 mixed (`ai_scaling_u_shape`, the
  saturated task from yesterday's run). Almost all tasks are multi-feature
  derivative targets (e.g. `FEATURE_NAMES=['t','N','P','R'] → dN_dt`).
- **17 / 25 flagged high artifact risk**, for two distinct reasons:
  - **unstable reward** — `var_test/var_train` as low as **6.9e-06**
    (`nuclear_and_particle_physics_0_001`), 3.3e-05, 8.4e-05 … On those, a tiny
    absolute error becomes an enormous negative R². haiku scored **−2.5e8** on one
    trial and **−2731** on another. These are metric artifacts, not 8-orders-of-magnitude
    differences in physics.
  - **saturation** — 3 tasks are already solved by a dumb baseline
    (`Mechanics_001_gen12`: RandomForest 0.99974; `quantum_mechanics_0_007`:
    poly deg-2 0.99937; `ai_scaling_u_shape`: RandomForest 0.999999).
- On 8 tasks **no dumb baseline beats the mean at all** (best k-NN/RF scores
  −0.02 to −3.65), confirming these holdouts demand real extrapolation.

**This is why the report leads with per-task medians and clipped R², never a raw
mean.** A mean over raw rewards on this set is dominated entirely by the worst
variance-collapsed task.

---

## 3. Independent verification (`harbor_run/rescore_b828.py`)

I re-ran every extracted `law.py` on the host against the same holdout:
**150 / 150 executed, 149 reproduced the official reward** to within 1e-4.

Getting this right required reading the verifier carefully: this 8.28 template
calls `law()` **one row at a time, in randomised order, inside a
privilege-dropped subprocess**, while the hidden CSV is temporarily moved out of
reach (`isolated_predictions`). My first pass called `law()` with all 500 rows at
once and 13 laws appeared to fail — they return a single prediction per call,
which is correct under the real contract. The per-row convention fixed all 13.

**The one genuine mismatch is itself a finding.** haiku's `Biology_gen5_v4` trial
(`__CdnYdVZ`) submits a law that tries to `pickle.load` a **pre-trained
GradientBoostingRegressor** from `.model_cache.pkl` and falls back to an
analytical formula when the file is absent. Official reward −1.918; my host
rescore of the fallback path −1.054. Either way it is not a discovered law.

Fixed-scale R² (same SSE ÷ `var_train`, immune to holdout variance collapse):
opus median **0.99999**, mean 0.990; haiku median 0.99669, mean 0.837. The medians
look close because the median task is easy for both; the **means** show where they
diverge, and the per-task table below shows it plainly.

---

## 4. Per-task results (median clipped R² over 3 attempts)

Sorted by opus's margin. `risk` = artifact risk from §2.

| task | risk | opus | haiku | margin | win |
|---|---|---|---|---|---|
| `m2_quantum_mechanics_0_003` | high | 1.0000 | −1.0000 | 2.0000 | opus |
| `m2_nuclear_and_particle_physics_0_001` | high | 1.0000 | −1.0000 | 2.0000 | opus |
| `m2_epidemiology_and_disease_dynamics_0_005` | high | 0.9767 | −1.0000 | 1.9767 | opus |
| `PSEv4_nonlinear_cubic_oscillator` | high | 0.9767 | −1.0000 | 1.9767 | opus |
| `Biology_gen5_v4` | none | 0.7503 | −1.0000 | 1.7503 | opus |
| `PSEv4_m1_biology_0_004_gen5` | high | 0.9945 | −0.3764 | 1.3709 | opus |
| `m2_physiology_and_homeostasis_0_004` | high | 0.9991 | −0.2156 | 1.2147 | opus |
| `SRBench0728_PopulationEcology_009_gen5` | high | 0.1752 | −1.0000 | 1.1752 | opus |
| `m2_classical_mechanics_0_001` | high | 0.9879 | −0.0796 | 1.0675 | opus |
| `SRBench0728_PopulationEcology_006_gen8` | none | 0.9999 | 0.0241 | 0.9758 | opus |
| `m2_cell_biology_and_signaling_0_000` | high | 0.9845 | 0.1111 | 0.8734 | opus |
| `Physics_42_000_gen5_v4` | high | 1.0000 | 0.6554 | 0.3446 | opus |
| `Economy_gen5_v4` | none | 0.7981 | 0.5955 | 0.2027 | opus |
| `m2_classical_mechanics_0_006` | none | 1.0000 | 0.8140 | 0.1860 | opus |
| `SRBench0728_Mechanics_002_gen15` | none | 1.0000 | 0.9295 | 0.0705 | opus |
| `m2_enzyme_kinetics_and_biochemistry_0_005` | high | 0.9983 | 0.9368 | 0.0614 | opus |
| `m2_quantum_mechanics_0_007` | high | 1.0000 | 0.9416 | 0.0584 | opus |
| `m2_epidemiology_and_disease_dynamics_0_000` | high | 0.9999 | 0.9720 | 0.0279 | opus |
| `m2_classical_mechanics_0_009` | none | 0.9999 | 0.9734 | 0.0265 | opus |
| `PSEv4_system_20260603_170953` | none | 1.0000 | 0.9852 | 0.0148 | opus |
| `SRBench0826_ai_scaling_u_shape_000` | high | 1.0000 | 0.9868 | 0.0132 | opus |
| `m2_population_ecology_0_002` | none | 0.9999 | 0.9890 | 0.0110 | opus |
| `m2_population_ecology_0_004` | high | 1.0000 | 0.9964 | 0.0036 | opus |
| `SRBench0728_Mechanics_001_gen12` | high | 1.0000 | 0.9993 | 0.0007 | opus |
| `SRBench0728_Mechanics_000_gen5` | high | −1.0000 | −1.0000 | 0.0000 | tie |

**The tie is not a tie.** On `Mechanics_000_gen5` both clip to −1, but the raw
medians are opus **−4.55** vs haiku **−1566.03** — a **344×** difference that
clipping erases. No dumb baseline beats the mean on that task either (best k-NN
−3.56), so it is simply hard for everyone; opus is much less wrong.

**Restricting to the 8 tasks with no artifact risk** — the cleanest read —
opus wins **8 / 8**, macro-mean 0.944 vs 0.539.

**Consistency:** opus's *worst* of 3 attempts beats haiku's *best* of 3 on
**18 / 25 tasks**. opus's median across-attempt spread is 0.0013 versus haiku's
0.268 — opus is not just better on average, it is ~200× more reproducible.

---

## 5. Qualitative differences in submitted laws

Applying the form checks that mattered on yesterday's `ai_scaling_u_shape` run:

- **Interpolators / lookup tables: 0 in all 150 laws, both models.** Yesterday
  haiku's best score came from a `CubicSpline` over 100 memorized training knots.
  Here that strategy is worthless because the holdouts extrapolate — the benchmark
  design closes the loophole on its own.
- **sklearn regressors: haiku 2, opus 0.** haiku submitted a
  `GradientBoostingRegressor` (via pickle) on `Biology_gen5_v4` and another
  sklearn-based law on `Mechanics_001_gen12`. Neither is a closed-form law.
- **Parsimony:** median count of multi-digit numeric literals is 7 (opus) vs 12
  (haiku); maxima are comparable (58 vs 56). Both mostly wrote genuine formulas.

---

## 6. Recommendations for the benchmark

1. **Fix the 17 artifact-prone tasks.** The dominant failure is holdout variance
   collapse: with `var_test/var_train` at 6.9e-06, R² reports numerical
   coincidence, not skill. Either normalize against a fixed scale (train variance
   or a physical scale) or reject tasks at generation time when
   `var_test/var_train < 1e-2`.
2. **Clip, or report raw and clipped side by side.** Unclipped rewards of −2.5e8
   destroy any mean. But note clipping *also* hides real gaps (§4's 344×) — so
   publish both, plus a log-scale view for the negative tail.
3. **Retire or repair the 3 saturated tasks** (`Mechanics_001_gen12`,
   `quantum_mechanics_0_007`, `ai_scaling_u_shape`): a dumb baseline already
   scores >0.999, so they cannot discriminate.
4. **Ship the difficulty ladder with each task.** `audit_b828_tasks.py` computes
   it in one pass; publishing "best dumb baseline = X" next to each reward would
   make results self-interpreting.
5. **Consider forbidding pickled/fitted ML models** in `law.py`, or check for
   them. The instruction asks for a closed-form law; a pickled
   GradientBoostingRegressor satisfies the verifier's interface but not the task.
6. **Keep the per-row randomised `isolated_predictions` design** — it is a real
   improvement over the older batch verifier: it blocks reading the hidden CSV and
   defeats order-dependent cheats.

---

## 7. Reproducing

```bash
# stage: 25 valid task dirs out of the zip (it also contains reports, a nested
# zip, and __MACOSX cruft that must not reach harbor)
unzip -q Bench_test_8.28.zip -d /tmp/b828 -x "__MACOSX/*" "*.DS_Store"

# haiku-4.5
TASKS_DIR=/data1/SRBench/outputs/harbor_tasks_b828 \
  JOB_NAME=b828_haiku45 PRESET=haiku-4.5 PROXY_PORT=8789 \
  STATEFILE=/tmp/srbench_haiku_proxy.json MODEL=claude-haiku-4-5 \
  N_ATTEMPTS=3 N_CONCURRENT=4 ./harbor_run/run_srbench_harbor.sh

# opus-4.8 (own port so both run side by side)
TASKS_DIR=/data1/SRBench/outputs/harbor_tasks_b828 \
  JOB_NAME=b828_opus48 PRESET=opus-4.8 PROXY_PORT=8788 \
  STATEFILE=/tmp/srbench_opus_proxy.json MODEL=claude-opus-4-8 \
  N_ATTEMPTS=3 N_CONCURRENT=4 ./harbor_run/run_srbench_harbor.sh

python3 harbor_run/audit_b828_tasks.py        # metric artifacts, per task
python3 harbor_run/extract_b828_outputs.py outputs/harbor_jobs harbor_run/b828_outputs
python3 harbor_run/rescore_b828.py            # independent re-scoring
```

**Operational notes.** Run the audit *after* the trials, or `nice` it: its
numpy/sklearn fits pushed load to 74 on 16 cores while trials were running (I
stopped it and re-ran later; no trial was harmed, 0 exceptions). Also, agents
writing scratch files into the tasks dir is harmless — harbor discovers by
directory, and it found exactly 25 — but clean them before archiving. And never
wrap `harbor run` in `timeout`: a killed trial still bills but scores 0.
