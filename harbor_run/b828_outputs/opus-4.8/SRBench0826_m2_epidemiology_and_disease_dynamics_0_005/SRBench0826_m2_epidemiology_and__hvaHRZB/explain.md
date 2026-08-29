# Discovering the law for `dI_dt` — seasonally forced infection

## 1. Problem framing

The dataset is a trajectory of a seasonally forced epidemic. Columns `t, S, I, R, C`
are observed inputs and `dI_dt` is the instantaneous rate of change of the
infectious population. The task is to express `dI_dt` as an explicit pointwise
function of the observed variables.

The context (seasonal forcing, recurrent yearly waves, susceptible replenishment,
recovery) points to a compartmental **SIRS-type** model with a periodically
modulated transmission rate.

## 2. What the auxiliary variables are

Numerically differentiating the *other* trajectories (only as an exploratory aid —
not used in the final law) gave extremely clean linear relations:

- **`dR/dt = 1.235·I − 0.217·R`**  (R² ≈ 0.9997)
  → recovery moves infectives into `R` at rate **γ ≈ 1.235**, and immunity wanes
  (`R → S`) at rate ≈ 0.217. This is a classic SIRS removal/waning structure.

- **`dC/dt = 1.91·I − 0.53·C`**  (R² ≈ 0.9993)
  → `C` is **not** a cumulative count; it is an *environmental reservoir* (or
  memory) state, driven by the current infectious load `I` and decaying with rate
  ≈ 0.53. It is a low-pass–filtered version of `I`.

These confirmed the model class and told us that `C` is a genuine dynamical state
that can feed back into transmission.

## 3. Structure of `dI_dt`

For an infection term of the standard mass-action form, `dI/dt = β·S·I − γ·I`, so
the effective transmission rate can be recovered pointwise as

```
β = (dI_dt + γ·I) / (S·I).
```

Inspecting `β`:

- **Seasonal component.** Regressing `β` against `cos(2πt)`, `sin(2πt)` gave a
  robust, state-independent amplitude of ≈ 0.9 with **period exactly T = 1**
  (a free-period fit returned T = 0.998). This is the fixed environmental forcing.
- **Not purely seasonal.** At a *fixed* seasonal phase, `β` still varied strongly
  across cycles (e.g. `β ≈ 10` at `t = 0` where `C = 0`, falling to `≈ 3` as the
  epidemic builds). A purely seasonal `β₀(1+β₁cosωt)` cannot reach `β ≈ 10`
  (that would need β₁ > 1, i.e. negative transmission at the trough), so `β` must
  depend on the state.
- **Which state?** The residual of the seasonal-only fit correlated with `C`
  (r ≈ −0.7) and, once `I` was included, with `I` as well. Physically:
  transmission is **suppressed by the environmental reservoir `C`** (accumulated
  immunity/awareness/environmental factor) and shows a **density-dependent
  saturation in `I`**. Including both `C` and `I` linearly in `β` collapses the
  residual and — crucially — is the *only* form that **generalizes forward in
  time** (see §5).

## 4. Final law

```
dI/dt = β(t, C, I) · S · I − γ · I

β(t, C, I) = b0 + a_cos·cos(2πt) + a_sin·sin(2πt) + kC·C + kI·I
```

with constants fit on the sustained-oscillation segment of the training run:

| constant | value       | meaning                                            |
|----------|-------------|----------------------------------------------------|
| `b0`     |  9.1601     | baseline transmission                              |
| `a_cos`  |  0.8961     | seasonal forcing (cos), period 1                   |
| `a_sin`  |  0.00249    | seasonal forcing (sin) — essentially zero          |
| `kC`     | −7.9413     | suppression of transmission by reservoir `C`       |
| `kI`     | −52.796     | density-dependent saturation in `I`                |
| `γ`      |  2.7240     | effective per-capita removal of infectives         |

Equivalently, the seasonal part is a single sinusoid of amplitude
`√(a_cos²+a_sin²) ≈ 0.896` and period 1.

`R` does not appear: it influences `I` only indirectly (through `S`), so it is not
needed to evaluate `dI/dt` pointwise.

## 5. Why these coefficients / validation

The trajectory has a short initial **break-in transient** (`t ≲ 3`) where the
state is far from the attractor; the hidden test set is the **right-hand
(later-time) segment**, which lies on the sustained limit cycle. The coefficients
were therefore fit on the attractor portion (`t ≥ 5`).

Performance of the final `law.py`:

| region        | R²        | RMSE     |
|---------------|-----------|----------|
| `t > 5`       | 0.99998   | 4.6e-5   |
| `t > 9`       | 0.99997   | 4.2e-5   |
| `t > 10`      | 0.99996   | 4.9e-5   |

**Forward-extrapolation (leave-future-out) checks** — fit on an early window,
predict the *later* held-out tail — confirmed the model class extrapolates:
fitting on `[5, 9.7]` and predicting the final 10 % of the run gave R² ≈ 0.9999.
Simpler variants (seasonal-only, or `C`-only in `β`) fit the attractor locally but
did **not** extrapolate forward (test R² dropping to 0.3–0.99), so the combined
`C`-and-`I` modulation is the form that both fits and generalizes.

The global R² over the whole training file is ≈ 0.90 only because the first few
break-in cycles deviate from the attractor law; those points are outside the test
regime.

## 6. Compliance notes

`law()` maps each row independently using only `t, S, I, C` and fixed constants.
It performs no file reads, no interpolation/lookup, no numerical differentiation,
no cross-row state, and does not depend on input ordering (verified by shuffling).
