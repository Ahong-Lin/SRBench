# SRBench v6 Candidate Generation Run — 2026-08-26

Candidate-only round: **137 of 147** requested symbolic-regression candidates were
generated. No Harbor task, no solver invocation, and no R² was computed or used to
filter — verified by audit (see *Harbor/solver isolation* below).

Repo state: fresh clone of `origin/main` at `8a468fe` ("Separate candidate
generation and add domain-aware evolution"), plus the three pipeline patches
described in *Patches applied*.

---

## 1. Results per discipline

| Discipline | gen0 requested | gen0 produced | candidates | missing |
|---|---|---|---|---|
| Physics | 70 | **70** | **67** | 3 |
| Biology | 70 | **70** | **63** | 7 |
| AI | 7 | **7** | **7** | 0 |
| **Total** | **147** | **147** | **137** | **10** |

All 137 candidates pass the hard gates: `mode=candidate`, `novelty.answer=Yes`,
`accepted_generations >= 5`, exactly 5000 data rows, exactly one CSV (no
train/test split), `evaluation_status=not_evaluated`.

Evolution depth: 134 candidates accepted at gen 5; three needed more because
novelty initially returned No — `quantum_mechanics_0_003` and
`nuclear_and_particle_physics_0_002` at gen 10, `physiology_and_homeostasis_0_005`
at gen 8. That is the intended "keep evolving until Yes or max-steps" behaviour.

Equation types: 76 `ode_system`, 58 `explicit`, 3 `implicit`.

### Per-subfield coverage

**Physics** (first 7 taxonomy subfields, 10 gen0 each)

| Subfield | gen0 | candidates | missing |
|---|---|---|---|
| classical_mechanics | 10 | 10 | 0 |
| electromagnetism | 10 | 10 | 0 |
| quantum_mechanics | 10 | 9 | 1 |
| statistical_mechanics_and_thermodynamics | 10 | 10 | 0 |
| fluid_dynamics | 10 | 9 | 1 |
| condensed_matter_physics | 10 | 9 | 1 |
| nuclear_and_particle_physics | 10 | 10 | 0 |
| **total** | **70** | **67** | **3** |

**Biology** (first 7 taxonomy subfields, 10 gen0 each)

| Subfield | gen0 | candidates | missing |
|---|---|---|---|
| population_ecology | 10 | 10 | 0 |
| enzyme_kinetics_and_biochemistry | 10 | **5** | **5** |
| neuroscience_and_neural_dynamics | 10 | 8 | 2 |
| genetics_and_population_genetics | 10 | 10 | 0 |
| cell_biology_and_signaling | 10 | 10 | 0 |
| epidemiology_and_disease_dynamics | 10 | 10 | 0 |
| physiology_and_homeostasis | 10 | 10 | 0 |
| **total** | **70** | **63** | **7** |

**AI** — `scaling_laws`, 7 fixed seeds, 7 candidates, complete.

### AI seed integrity (audited)

The 7 AI records are byte-identical to `seeds/ai_scaling_laws_equations.jsonl`
after stripping the one added bookkeeping key (`generation_mode: "fixed"`);
per-field sha256 comparison shows zero drift. `run_meta.json` records
`equation_mode=fixed` with `fixed_equation_sha256=6b3d0608f2c8…`, independently
recomputed and matching. No Stage-2/Stage-3 LLM ran for AI:
`_run_fixed_equation_import` returns from `main()` before either `ModelCaller` is
constructed, the AI `run_meta` lacks all 20 LLM-provenance keys that
physics/biology carry, `equation_failures.jsonl` is 0 bytes, and there is no
`runlogs/gen0_AI*.log`. No extra equations were fabricated.

---

## 2. Failures: 10 gen0 equations produced no candidate

All 10 exhausted `--max-lineage-attempts 4`. Stage is `evolve` for every one —
none failed at DataSpec or data generation.

| ID | Discipline | Stage | Error |
|---|---|---|---|
| `m2_fluid_dynamics_0_008` | physics | evolve | `static equations must have 1-4 V inputs` |
| `m2_quantum_mechanics_0_008` | physics | evolve | `condition_promotion must add exactly one V input` |
| `m2_condensed_matter_physics_0_009` | physics | evolve | `state 'u' RHS uses undeclared/non-state symbols: g_damp` |
| `m2_neuroscience_and_neural_dynamics_0_002` | biology | evolve | `law_refinement cannot add/remove V inputs` |
| `m2_neuroscience_and_neural_dynamics_0_005` | biology | evolve | `add_term must not add/remove V inputs` |
| `m2_enzyme_kinetics_and_biochemistry_0_000` | biology | evolve | `law_refinement cannot add/remove V inputs` |
| `m2_enzyme_kinetics_and_biochemistry_0_001` | biology | evolve | `regime_change cannot add/remove V inputs` |
| `m2_enzyme_kinetics_and_biochemistry_0_006` | biology | evolve | `law_refinement cannot add/remove V inputs` |
| `m2_enzyme_kinetics_and_biochemistry_0_009` | biology | evolve | `regime_change cannot add/remove V inputs` |
| `m2_enzyme_kinetics_and_biochemistry_0_010` | biology | evolve | `law_refinement cannot add/remove V inputs` |

Failure directories retain `manifest.json` + `lineage_attempts.jsonl` for audit,
but no `final_spec.json` and no CSV.

### Root cause: Stage 2 mislabels intrinsic constants as observable inputs

Nine of the ten failures share one cause. Stage 2 assigned role `V`
(observable input) to symbols that are physically **parameters**: `Vmax`, `Km`,
`Ki`, `Ka1`, `Ka2`, `Ksi`, `r_max`, `lambda`, `V0`, `alpha`, `beta`. The evolver
correctly tries to demote them, but `equation_evolve` forbids changing the V set
under *every* operator (`add_term`, `law_refinement`, `regime_change`,
`condition_promotion`), so all four lineages die on the same rule. Records already
at the 4-input cap (`MAX_STATIC_INPUTS_DEFAULT`) fail symmetrically — no room to
promote a condition.

An audit of all 147 gen0 records found **12 carrying suspicious V labels**,
concentrated in `enzyme_kinetics_and_biochemistry` (6/10) and
`neuroscience_and_neural_dynamics` (2/10) — which is exactly where the coverage
shortfall lands. Michaelis-Menten-family scenarios are the systematic offender:
`Vmax`/`Km` read like measurable quantities to the scenario generator.

The tenth failure (`condensed_matter_physics_0_009`) is a different structural
ceiling: an ODE system already at the 4-state cap (`MAX_ODE_STATES`), so every
`change_assumption` promoting an internal quantity to a state is rejected, and the
model's workarounds leave dangling symbols (`g_damp`, `kappa_th`, `tau_S`).

Retrying either class unchanged cannot succeed. Fixing them means editing gen0
`symbol_properties` (`V` → `P`), which changes the benchmark's input set — a
scientific decision, so it was **not** done unilaterally. Doing so would plausibly
recover 9 of the 10.

### One failure was transient and was recovered

`m2_nuclear_and_particle_physics_0_008` initially failed differently: all four
lineages reached `novelty=Yes`, then died in the DataSpec agent on
`Reached maximum number of turns (18)`. Raising `--spec-max-turns 40` moved the
wall to a hardcoded `$2.50` budget cap; making that env-overridable
(`SRBENCH_SPEC_MAX_BUDGET_USD=8`) let it complete. It is included in the 137, and
is the reason the total is 137 rather than 136.

---

## 3. Data-quality defects in the delivered 137

An independent 6-dimension audit with adversarial verification found defects that
the pipeline's own gates did not catch. **These candidates are delivered as-is;
screen them before use.**

### Blockers — 3 candidates unusable as scored tasks

| Candidate | Defect |
|---|---|
| `m2_nuclear_and_particle_physics_0_005` | Target `B_per_A` is **100 % NaN** (5000/5000). The pairing term uses `(-1)**Z` and `(-1)**(A-Z)`, but `A` and `Z` are sampled as **continuous floats**, so a non-integer exponent on −1 is complex → NaN. Inputs are finite, so the CSV looks structurally valid; there is zero target signal. |
| `m2_fluid_dynamics_0_004` | **23.5 % of rows (1176/5000) are not roots of the spec's own `g()=0`.** `fsolve` silently failed to converge in a contiguous band `Ar ∈ [1.020, 1.489]`; residuals reach 0.333 against `sigma=0.003` (~100× noise). Independently reproduced. |
| `m2_statistical_mechanics_and_thermodynamics_0_006` | Target `m` is **2.5 % NaN** (125/5000). `(1 − T/(Tc·(1+kappa_p·P)))**0.35` takes a fractional power of a negative base when `P < 0`. |

### Major — benchmark-validity issues

- **Shared noise draw across 119 of 134 candidates.** After dividing each
  residual by its own sigma, 119 candidates collapse to one bit-identical vector
  of 5000 unit normals. Cause: `evolution_pipeline.py` seeds generation with
  `args.seed + attempt`, and every batch run used the default `--seed 0`, so every
  first-attempt success drew from seed 1. Independently reproduced (largest
  identical group = 119). Noise is therefore correlated across the benchmark
  rather than independent per task.
- **5 candidates with noise at or above signal scale.** Absolute sigma was chosen
  without reference to target scale, capping achievable R² below any plausible
  threshold: `neuroscience_and_neural_dynamics_0_004` (rel. noise 3.63),
  `neuroscience_and_neural_dynamics_0_006` (1.43),
  `epidemiology_and_disease_dynamics_0_002` (0.87),
  `neuroscience_and_neural_dynamics_0_000`, `population_ecology_0_006`. Note the
  verifier partly refuted the "blocker" reading: Harbor scores
  `benchmark_output`, i.e. the **clean** column, so the noisy column may never be
  scored. Impact depends on the evaluation protocol chosen later.
- **1 dead ODE state.** `classical_mechanics_0_009` state `e` is provably inert —
  the three parameters carrying it (`nu_hyst`, `delta_nu`, `delta_A`) are all
  exactly 0.0, so removing `e` changes the target by exactly 0. A further 23
  `ode_system` candidates have a non-target state whose total influence on the
  target is below one sigma.
- **2 no-op generations.** `ai_scaling_parallel_000` gen4 and
  `ai_scaling_data_constrained_000` are byte-identical to their parent despite a
  `change_summary` claiming a substantive edit — the lineage is one effective
  generation shorter than recorded.
- **1 metadata stub.** `nuclear_and_particle_physics_0_008` (the recovered retry)
  is the only spec with `noise=0.0` and therefore the only CSV with **no
  `*_noisy` column**; `rationale`, `excitation_report`, `sanity_expectations` are
  empty. Downstream consumers expecting a noisy column will find none.

### Clean

- Row counts: 137/137 have exactly 5000 rows.
- One CSV per candidate: 137/137 — no train/test split anywhere.
- Duplicate rows: **zero** across all candidates (5000/5000 unique input rows).
- Lineage integrity: every `accepted_lineage.jsonl` has contiguous generations
  `0..N` with no gaps or duplicates, and every gen0 exactly matches its source
  record in `equations.jsonl`.
- Spec structure: 0 `equation_type`/`integrator` mismatches; all 76 `ode_system`
  specs have aligned `state_variables`/`state_rhs`/`initial_conditions` with the
  target state present and every state emitted as a CSV column; all 237
  independent-variable ranges are finite and strictly increasing.

### Harbor / solver isolation — verified clean

No `task.toml`, `instruction.md`, `solve.sh`, `test_outputs.py`, `solver_*.json`,
`train_data.csv` or `test_data.csv` anywhere under `outputs/Candidate_Equations`.
All manifests carry `mode=candidate` with `train_points`, `hidden_test_points`,
`easy_r2`, `solver_command_template` all `null`. Audit statuses are only
`candidate_generated` / `reject_not_novel` / `pipeline_error` — no `accept`, no
`reject_too_easy_after_replan`, no `solver` keys. The one `*train*.csv` glob hit is
a false positive from the substring in `ai_scaling_data_cons(train)ed_000_*.csv`.

---

## 4. Output locations

```
outputs/Scenarios/{physics,biology,AI}_fixed_main/    # subfields.json, scenarios.jsonl
outputs/Equations/{physics,biology,AI}_fixed_main/    # equations.jsonl (gen0), run_meta.json
outputs/Candidate_Equations/candidate_<scenario_id>_<timestamp>/
    manifest.json                       # mode=candidate, nulls where Harbor would go
    final_spec.json                     # DataGenSpec + finalization block
    final_result.json
    lineage_attempts.jsonl              # per-attempt audit trail
    lineage_attempt_NN/
        candidate_spec.json
        candidate_data/*.csv            # the single 5000-point dataset
        candidate_data/*.png            # diagnostic plot
        accepted_lineage.jsonl          # gen0..genN records
        accepted_lineage.xlsx
        novelty.json
runlogs/                                # gen0 logs, per-candidate batch logs, progress.json
```

Directories that exist without a `final_spec.json` are the 10 failures (plus two
superseded attempt dirs for `nuclear_and_particle_physics_0_008`).

---

## 5. How this was run

Provider: opus-4.8 through a **local Bedrock-passthrough proxy** on port 8801
(`proxy_daemon.py --preset opus-4.8`), driven with `--provider anthropic`. The WOA
model-eval OpenAI gateway was unusable — 10 consecutive retries all returned 429.
The local proxy sustained 13-way concurrency at ~2.5 s/call with no throttling.

```bash
# gen0 — Physics / Biology (Stage 1-3; --resume tops up failures)
./run_gen0.sh physics physics_fixed_main
./run_gen0.sh biology biology_fixed_main --resume

# gen0 — AI (fixed seed import, no LLM)
python3 auto_workflow.py --subject AI --subfield-source fixed --run-name AI_fixed_main

# one candidate
./run_candidate.sh outputs/Equations/<run>/equations.jsonl <scenario_id> <discipline>

# whole discipline, N at a time (skips completed, so re-runnable)
WORKERS=5 ./run_candidate_batch.sh outputs/Equations/physics_fixed_main/equations.jsonl \
    physics runlogs/batch/physics

# status + failure classification
python3 report_progress.py
```

Reaching 70 gen0 per subject took 5 `--resume` passes each. Four scenarios failed
**deterministically** rather than transiently and had to be pruned from
`scenarios.jsonl` so `--resume` would regenerate replacements: three declared
`Vmax`/`Ka`/`Tc`/`Delta0` as observable inputs, and one (a Debye heat-capacity
scenario) inherently requires an `Integral`, which the validator rejects. This is
why some scenario ids carry suffixes above `_009` — per-subfield counts remain
exactly 10.

### Patches applied

Three fixes were required; the run cannot reproduce without them.

1. **`auto_workflow.py` — no throttle backoff.** It carries its own duplicate
   `ModelCaller`, and `_retryable_errors()` omits `anthropic.RateLimitError`. Its
   per-stage retry loops also re-prompt with **no sleep**, so a throttled batch
   burned all attempts in under a second — both gen0 runs crashed on the first 429
   burst. Added `_with_throttle_backoff()` around both transports.
2. **`model_provider.py` — anthropic branch had no retry at all** (only the SDK's
   two quick ones), and the openrouter branch used full jitter (`delay * random()`),
   which can wait ~0 s. Both now use `_backoff_seconds()` =
   `min(60, 2**n) * (0.5 + rand)`.
3. **`data_spec_agent_sdk.py` — `$2.50` spec budget was hardcoded** with no CLI
   flag. Now overridable via `SRBENCH_SPEC_MAX_BUDGET_USD`; this recovered
   `nuclear_and_particle_physics_0_008`.

Env knobs: `SRBENCH_THROTTLE_MAX_RETRIES`, `SRBENCH_ANTHROPIC_MAX_RETRIES`,
`SRBENCH_OPENROUTER_MAX_RETRIES` (default 10), `SRBENCH_SPEC_MAX_BUDGET_USD`
(default 2.5).

The DataSpec stage additionally needs a `claude` binary on PATH: the Agent SDK
spawns that exact name, and this host provides only `tclaude` (a shell function,
invisible to `shutil.which`). `bin/claude` is a two-line shim.

---

## 6. Recommended follow-ups

1. **Drop or regenerate the 3 blocker candidates** before any evaluation —
   especially `nuclear_and_particle_physics_0_005` (100 % NaN target).
2. **Decide on the 9 mislabeled-V gen0 records.** Flipping `Vmax`/`Km`/`Ki`/… from
   `V` to `P` in `equations.jsonl` and re-running would plausibly bring the total
   to ~146, but it changes each task's input set.
3. **Fix the shared noise seed** — pass a distinct `--seed` per scenario so noise
   is independent across the benchmark.
4. **Make noise relative to target scale**, not absolute, so sigma cannot exceed
   signal std.
5. **Add generator-side guards** for the two defect classes the gates missed:
   assert the target column is finite, and check `fsolve` convergence for
   `implicit` specs instead of accepting whatever it returns.
