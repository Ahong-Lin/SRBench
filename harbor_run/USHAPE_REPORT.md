# SRBench0826_ai_scaling_u_shape_000 — opus-4.8 vs haiku-4.5

Run date: 2026-08-28. Task: `SRBench0826_ai_scaling_u_shape_000.zip` (harbor /
terminal-bench format, single task, `difficulty = "hard"`).
Runner: `harbor_run/run_srbench_harbor.sh` (local Docker, one container per trial,
hyra Anthropic-compat proxy → internal gateway). **3 attempts per model** (`-k 3`),
because a single task gives one coin flip and the interesting question here is
run-to-run consistency.

Jobs: `outputs/harbor_jobs/ushape_{opus48,haiku45}` (gitignored).
Extracted artefacts + scores: `harbor_run/ushape_outputs/` (committed).

---

## 1. Headline scores (official metric)

| model | trial | official reward (test R²) | test RMSE | cost |
|---|---|---|---|---|
| opus-4.8 | `5J2obzY` | **1.000000** | 5.71e-05 | $2.44 |
| opus-4.8 | `AsaLUGT` | 0.999994 | 2.12e-04 | $1.53 |
| opus-4.8 | `auiNu3w` | 0.999994 | 2.08e-04 | $1.62 |
| haiku-4.5 | `T3h35vs` | **1.000000** | 2.49e-07 | $0.39 |
| haiku-4.5 | `HwENnwJ` | 0.999858 | 1.03e-03 | $0.31 |
| haiku-4.5 | `NDBJbZj` | 0.999858 | 1.03e-03 | $0.29 |

| | opus-4.8 | haiku-4.5 |
|---|---|---|
| trials / errors | 3 / 0 | 3 / 0 |
| mean reward | 0.999996 | 0.999905 |
| median reward | 0.999994 | 0.999858 |
| worst reward | 0.999994 | 0.999858 |
| wall clock | 15m 35s | 4m 16s |
| total cost | $5.59 | $0.99 |

Both models pass on every attempt, 0 exceptions, 0 retries. Every submitted
`law.py` re-imports and re-scores cleanly outside the container, and my
independent rescoring reproduces all six official rewards to 6 d.p.

**Taken at face value this reads as a tie: 0.999996 vs 0.999905, both ≈1.0.
That reading is wrong, and the rest of this report is why.**

---

## 2. The task cannot discriminate on its own metric

Three properties of this task, each verified numerically
(`harbor_run/diagnose_ushape.py`, output in `ushape_outputs/diagnosis.json`):

**(a) The data is noise-free.** The reference law in `solution/solve.sh`
reproduces both CSVs to a residual std of **3.8e-17** — floating-point dust.
There is no irreducible error, so R² is bounded only by how finely you can trace
a known-smooth curve.

**(b) The holdout is interpolation, not extrapolation.** `train_data.csv` (4500
pts) and `tests/test_data.csv` (500 pts) are a **single uniform 5000-point grid
on [-3, 3] split 90/10**; union spacing is a constant 1.2002e-03. Every test
point lies within **0.0012** of a training point, and 499/500 are strictly inside
the training hull. `var_test/var_train = 1.0097`.

This is the *opposite* of the earlier SRbench_8_6 / 8.23 sets, where holdouts were
right-extrapolation segments with variance collapse (`var_test/var_train` down to
8.6e-05) that made rewards like −99999 and −1.5e6 metric artifacts. **Here the
`variance < 1e-12 → nmse = 100000` sentinel is unreachable and the official R²
is trustworthy as far as it goes.** The problem is no longer a broken metric —
it is a metric measuring the wrong thing.

**(c) Dumb baselines already saturate it.** Test R² with no symbolic discovery
whatsoever:

| baseline | test R² |
|---|---|
| constant (train mean) | −0.000007 |
| poly deg 2 | 0.466286 |
| poly deg 3 | 0.730194 |
| poly deg 5 | 0.851983 |
| poly deg 8 | 0.951504 |
| poly deg 12 | 0.984035 |
| **poly deg 20** | **0.999858** |
| CubicSpline, 20 knots | 0.999973 |
| CubicSpline, 50 knots | 1.000000 |
| CubicSpline, all 4500 knots | 1.000000 |
| RandomForest(100) | 0.999999 |

Note the exact coincidence: **poly deg 20 scores 0.999858 — bit-for-bit the score
of haiku's two lower trials.** And a 50-knot spline scores a perfect 1.000000,
matching the top score of *both* models. On a noise-free, densely-sampled,
in-range holdout, memorizing the curve is not merely competitive with discovering
it — it wins. The metric ranks a lookup table at or above a closed form.

---

## 3. What the models actually submitted

The scores hide a categorical difference in *kind* of answer.

**opus-4.8 — 3/3 closed-form, parsimonious, no interpolators.** All three
converged on the same family, `smooth baseline + a few localized Gaussian bumps`,
with 21–35 constants:

- `5J2obzY`: `c + A·exp(k·logC) + B·logC` + 4 Gaussians
- `auiNu3w`: cubic baseline + 5 Gaussians
- `AsaLUGT`: baseline + Gaussian/erf terms

None matches the reference parameterization (quadratic + tanh + logistic + cubic
+ Gaussian) term-for-term, but that is legitimate: they are numerically
equivalent re-parameterizations of the same smooth curve, reached by
`scipy.curve_fit` from a different basis. Each is a genuine formula a scientist
could read, differentiate, and interpret.

**haiku-4.5 — 0/3 closed-form.**

- `HwENnwJ` and `NDBJbZj`: a **degree-20 polynomial** — and *the identical
  coefficient vector in both trials*, down to the last digit
  (`3.216086548936672e-07·logC²⁰ + …`). Not a discovered law; the output of
  `np.polyfit(X, y, 20)`, twice.
- `T3h35vs` (the 1.000000 trial): a **`scipy.interpolate.CubicSpline` over 100
  hard-coded (logC, Brier) knots copied from the training data** — 204 numeric
  literals. This is a lookup table with interpolation. **It scored a perfect
  1.000000 and the best RMSE of all six trials (2.5e-07).**

haiku's best score came from the answer that does the least science.

---

## 4. The check that does discriminate

Since in-range fit is saturated, I evaluated each law against the analytic ground
truth on a grid 20× finer than train, and — the real probe — **just outside** the
observed range. Nothing in the task tests extrapolation, which is exactly why it
exposes memorization.

RMSE vs ground truth:

| model / trial | in-range [-3,3] | extrap [-4,-3] | extrap [3,4] | form |
|---|---|---|---|---|
| opus `5J2obzY` | 5.60e-05 | **3.49e-03** | **3.87e-02** | closed form |
| opus `AsaLUGT` | 2.10e-04 | 3.88e-02 | 3.24e-02 | closed form |
| opus `auiNu3w` | 2.08e-04 | 7.90e-03 | 1.55e-02 | closed form |
| haiku `T3h35vs` | **2.49e-07** | 1.71e-05 | 1.70e-03 | spline table |
| haiku `HwENnwJ` | 1.01e-03 | **1.27e+03** | **2.18e+03** | poly deg 20 |
| haiku `NDBJbZj` | 1.01e-03 | **1.27e+03** | **2.18e+03** | poly deg 20 |

haiku's two polynomial trials degrade by **six orders of magnitude** off the
training support (RMSE ~1e3 against a target of range ~0.35; R² ≈ −8.3e9). They
are numerically worthless one step outside the grid. opus's closed forms stay at
~1e-2 in the same region — imperfect, but the same order as the function itself.

Two honest caveats:

- haiku's spline (`T3h35vs`) extrapolates *well* here (1.7e-05 / 1.7e-03) and is
  the most accurate law in-range. A dense spline over noise-free data is a very
  good interpolant. It is still not a discovered law: it cannot be read,
  differentiated symbolically, or interpreted, and it carries 100 memorized data
  points. Judging it "best" is a judgement about the *metric*, not the science.
- opus `AsaLUGT` is the worst extrapolator among the closed forms on the left
  edge (R² = −6.8). Parsimony is not automatically good extrapolation.

**Conclusion.** On parsimonious, interpretable, closed-form recovery — the stated
goal — **opus-4.8 wins 3/3 vs 0/3.** On the official metric the two are
indistinguishable (0.999996 vs 0.999905). The gap between those two sentences is
the finding.

---

## 5. Recommendations for the benchmark

The metric artifact of the earlier sets (variance collapse on extrapolation
holdouts) has been fixed; this task's holdout is well-conditioned. But the
pendulum swung too far — an i.i.d. 90/10 split of one dense grid over noise-free
data is trivially interpolable, so R² saturates for everyone and the task
cannot deliver its `difficulty = "hard"` label. Concretely:

1. **Reject or downweight solutions containing interpolators / hard-coded data
   tables.** A static check for `CubicSpline`/`interp1d`/`UnivariateSpline` and a
   cap on numeric-literal count (opus: 21–35; haiku's spline: 204) separates the
   two classes cleanly and cheaply.
2. **Score on a held-out region, not a held-out sample** — e.g. train on
   logC ∈ [-3, 2], test on (2, 3]. Keep the variance from collapsing (the old
   bug) by checking `var_test/var_train > 1e-2` at generation time.
3. **Add noise (or report the noise-free property).** With σ = 0 there is no
   penalty for overfitting, which is what lets deg-20 poly score 0.999858.
4. **Report a difficulty ladder with every task.** If poly deg 20 already scores
   0.999858, a model scoring 0.9999 has demonstrated nothing. This is cheap to
   compute at generation time and would have flagged this task before it shipped.
5. **Consider a parsimony/interpretability term in the reward** (term count,
   symbolic complexity), since the instruction explicitly asks for a "closed-form
   relationship" but the verifier never checks for one.

---

## 6. Reproducing

```bash
# opus-4.8
TASKS_DIR=/data1/SRBench/outputs/harbor_tasks_ushape \
  JOB_NAME=ushape_opus48 PRESET=opus-4.8 PROXY_PORT=8788 \
  STATEFILE=/tmp/srbench_opus_proxy.json MODEL=claude-opus-4-8 \
  N_ATTEMPTS=3 N_CONCURRENT=3 ./harbor_run/run_srbench_harbor.sh

# haiku-4.5 (own port so both run side by side; EFFORT auto-empty for this preset)
TASKS_DIR=/data1/SRBench/outputs/harbor_tasks_ushape \
  JOB_NAME=ushape_haiku45 PRESET=haiku-4.5 PROXY_PORT=8789 \
  STATEFILE=/tmp/srbench_haiku_proxy.json MODEL=claude-haiku-4-5 \
  N_ATTEMPTS=3 N_CONCURRENT=3 ./harbor_run/run_srbench_harbor.sh

# pull law.py/explain.md out of verifier stdout, rescore, then diagnose
python3 harbor_run/extract_ushape_outputs.py outputs/harbor_jobs harbor_run/ushape_outputs
python3 harbor_run/diagnose_ushape.py
```

`law.py` is not persisted outside the container; `tests/test.sh` prints it fenced
between `---- LAW BEGIN/END ----` into `verifier/test-stdout.txt`, which is what
`extract_ushape_outputs.py` parses.
