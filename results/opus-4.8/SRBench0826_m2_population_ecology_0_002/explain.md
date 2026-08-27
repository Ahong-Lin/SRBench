# Discovered Law: Prey Dynamics in a Predator–Prey Reserve

## Result

The rate of change of the prey population `N` is governed by the
**Rosenzweig–MacArthur** predator–prey model — logistic prey growth combined
with a **Holling type II** (saturating) predation term:

```
dN/dt = r · N · (1 − N/K)  −  a · N · P / (1 + b · N)
```

with fitted parameters

| symbol | meaning                              | value      |
|--------|--------------------------------------|------------|
| `r`    | intrinsic prey growth rate           | 0.79803    |
| `K`    | carrying capacity of the reserve     | 99.9076    |
| `a`    | predator attack (encounter) rate     | 0.13054    |
| `b`    | handling / saturation coefficient    | 0.021947   |

## Fit quality

- **R² = 0.99984** on the full training set (RMSE ≈ 0.058, max abs. error ≈ 0.26 over a range of ~30).
- **R² = 0.99953** on a forward time-holdout: fit on the first 70 % of the
  time series, evaluated on the last 30 %. This mimics the hidden test set
  (the right-hand time segment), so the model extrapolates cleanly across the
  boom-and-bust cycles.

## How each term maps to the biology

- **`r · N · (1 − N/K)`** — In the predator's absence (`P = 0`) prey reproduce
  logistically: growth is exponential when rare and saturates as `N` approaches
  the reserve's carrying capacity `K ≈ 100`. The stable abiotic conditions of
  the enclosed reserve justify a fixed `K`.
- **`a · N · P / (1 + b · N)`** — Predation couples the two abundances through
  encounters (`∝ N·P`), but with a **saturating** (Holling type II) response:
  at high prey density each predator's consumption plateaus (`b·N` in the
  denominator), representing finite handling time / satiation. `a/b ≈ 5.95` is
  the asymptotic maximum kill rate per predator.

This functional response is what produces the characteristic recurring
boom-and-bust limit cycles rather than the damped orbits of the plain
Lotka–Volterra model.

## Why `R` and `t` are not used

- **`t`**: The system is autonomous — the law depends only on the current state
  `(N, P)`, not on absolute time. Adding `t` gave no meaningful improvement.
- **`R`**: Although `R` is strongly *correlated* with `N` (≈ 0.87) because it
  co-varies along the same trajectory, it carries **no independent predictive
  power**. After fitting the model in `(N, P)` only, the residuals correlate
  with `R` at just 0.056. Introducing resource-consumption terms such as `N·R`
  did not improve the fit, whereas the Holling type II form did. `R` is treated
  as a spectator variable (a co-evolving resource/auxiliary state), not a
  driver of `dN/dt`.

## Method

1. Loaded the data and inspected distributions and pairwise correlations.
2. Examined the **per-capita** growth rate `(dN/dt)/N`, which revealed a
   dominant `r − a·P` structure (Lotka–Volterra signature) plus density
   dependence in `N` — pointing to logistic growth + a functional response.
3. Compared candidate mechanistic forms by nonlinear least squares
   (`scipy.optimize.curve_fit`):
   - Logistic + linear predation (Lotka–Volterra): R² ≈ 0.83
   - **Logistic + Holling II (Rosenzweig–MacArthur): R² ≈ 0.99984** ✅
   - Beddington–DeAngelis (adds predator interference): R² ≈ 0.99989
     (negligible gain — rejected as over-parameterization).
4. Verified stability of the parameters under a forward time-holdout and
   confirmed `R`/`t` add nothing.

## Implementation

`law.py` implements `law(input_data)` which reads `N` and `P` from each record
and returns `{"dN_dt": r·N·(1−N/K) − a·N·P/(1+b·N)}`.
