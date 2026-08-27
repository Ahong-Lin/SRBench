# Discovered Law for `dN_dt`

## Final formula

```
dN/dt = r * N * ln(K / crowding_load)
      = N * (A + B * ln(crowding_load))
```

with parameters fitted (least squares on `dN_dt`) over the full training set:

| parameter | value |
|-----------|-------|
| A         |  2.039104 |
| B         | -0.299738 |
| r = −B    |  0.299738 |
| K = exp(−A/B) | 900.50 |

This is a **Gompertz growth law** in which the *delayed crowding density*
`crowding_load` plays the role of the regulating density, and the effective
carrying capacity is `K ≈ 900`.

Training fit: **R² = 0.949**, RMSE ≈ 19.2 (RMSE is dominated by the very
large-amplitude early transient where |dN/dt| reaches ~300).

## The full dynamical system

Two facts uncovered during analysis characterize the experiment:

1. **`crowding_load` is a low-pass / delayed copy of `N`.** A regression of its
   numerical time-derivative gives, to 8 significant figures,

   ```
   d(crowding_load)/dt = 0.2 * (N - crowding_load)   (R² = 0.99999999)
   ```

   i.e. the crowding signal relaxes toward the current population with time
   constant τ = 5.

2. **`N` grows in Gompertz fashion against that delayed density:**

   ```
   dN/dt = r * N * ln(K / crowding_load)
   ```

Together these produce the behaviour seen in the data: `N` overshoots, the
crowding term catches up with a lag, and the system executes a **damped
oscillation that spirals in toward the equilibrium `N = crowding_load = K ≈ 900`**
(the last training rows sit at N≈C≈891, dN/dt≈0). Because the regulator is
delayed, growth stays positive while `crowding_load < K` even when `N` is already
large, which is exactly what generates the oscillation.

## Methodology

1. **Data inspection.** Verified `dN_dt` equals the numerical derivative of `N`
   to ~1e-4, so the data are a clean (noise-free) ODE integration; any residual
   in a candidate law is model misspecification, not noise.

2. **Per-capita analysis.** The per-capita rate `g = dN/dt / N` is governed
   overwhelmingly by `crowding_load`. Testing candidate regulator shapes
   (`g = a + b·C`, logistic; `g = a + b·C²`; `g = a + b·ln C`, Gompertz; ratio
   and theta-logistic forms) showed the **logarithmic (Gompertz) form** describes
   the density dependence best.

3. **Extrapolation validation.** Because the hidden test set is a *later time
   segment* — the trajectory continuing to spiral toward its centre — I selected
   the law by **forward time-holdout**: fit on the left part of the series,
   score on the right. Across cut points (train t < 38, 43, 46), the Gompertz
   form `dN/dt = N·(A + B·ln C)` was consistently the **best and most stable
   extrapolator** (holdout R² up to ~0.69), beating polynomial/logistic
   alternatives that overfit the transient and diverged out-of-sample. Adding
   phase terms such as `(N − crowding_load)` improved the in-sample fit but
   *degraded* extrapolation, so they were rejected.

4. **Autonomy.** The law uses only state variables (`N`, `crowding_load`), not
   explicit `t`. Models using explicit time extrapolated catastrophically
   (holdout R² strongly negative), whereas the state-based Gompertz law remains
   valid beyond the observed window because it correctly encodes the approach to
   the `N = C = K` equilibrium.

## Caveats

The underlying system carries a small amount of dynamical structure that is not
a single-valued function of `(N, crowding_load)` alone (the inward spiral means
nearby `(N, C)` states are revisited on successive loops with slightly different
`dN/dt`). That residual (~a few units RMSE near equilibrium) is not recoverable
from the two observed state variables without introducing time-dependent terms
that do not extrapolate. The Gompertz law captures the dominant, physically
meaningful and extrapolation-safe part of the dynamics.
