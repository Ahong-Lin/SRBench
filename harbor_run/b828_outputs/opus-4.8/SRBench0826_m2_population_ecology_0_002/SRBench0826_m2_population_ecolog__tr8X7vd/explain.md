# Discovered Law: Prey Dynamics in a Predator–Prey Reserve

## Result

The instantaneous rate of change of the prey population `N` is governed by the
**Rosenzweig–MacArthur model** — logistic self-limited growth minus a Holling
type II (saturating) predation term:

```
dN/dt = r · N · (1 − N/K)  −  a · N · P / (1 + h · N)
```

with constants fit from the training data:

| symbol | meaning                      | value        |
|--------|------------------------------|--------------|
| `r`    | intrinsic prey growth rate   | 0.79802985   |
| `K`    | prey carrying capacity       | 99.9076146   |
| `a`    | predator attack/capture rate | 0.13054372   |
| `h`    | prey handling time           | 0.02194693   |

## Interpretation

- **`r·N·(1 − N/K)`** — logistic growth. In the predator's absence prey grow
  at per-capita rate `r ≈ 0.80`, but growth self-limits and stops at the
  carrying capacity `K ≈ 100` set by the enclosed reserve's fixed resources.
- **`a·N·P / (1 + h·N)`** — Holling type II functional response. The predation
  loss couples both abundances (`∝ P` and to prey through `N`), but *saturates*
  at high prey density: each predator needs handling time `h` per prey, so its
  intake plateaus at `a/(a·h)` regardless of how abundant prey become. This
  saturation is exactly what turns the classic neutral Lotka–Volterra cycles
  into the recurring boom-and-bust limit cycles the ecologists observe.

## How it was found

1. **Correlations / linear probes.** Plain Lotka–Volterra (`N`, `N·P`) explained
   only R²≈0.38. Adding a quadratic self-limitation term (`N`, `N²`, `N·P`) rose
   to R²≈0.83, pointing to logistic growth plus a *nonlinear* predation term.
2. **Nonlinear least squares.** Fitting the full Rosenzweig–MacArthur form
   `r·N·(1−N/K) − a·N·P/(1+h·N)` jumped to **R² = 0.99984** on the full training
   set, cleanly recovering the four parameters above.
3. **Held-out validation.** Fitting on the first half of the time series and
   predicting the *later* half (matching the hidden test set's structure) gave
   **R² = 0.99959**, confirming the law extrapolates in time rather than
   overfitting.
4. **Role of `R` and `t`.** The auxiliary observed variable `R` and time `t` add
   essentially nothing: residuals of the (N, P) model are ~0.06 in magnitude
   (pure measurement noise) and show only weak, non-structural correlation with
   `R` or `t`. They are therefore excluded — the dynamics are fully explained by
   `N` and `P`.

## Model quality

- Full training set: **R² = 0.99984**, RMSE = 0.058, max abs error = 0.256.
- Later-segment holdout: **R² = 0.99959**.

## Implementation notes

`law()` in `law.py` applies the closed-form expression above to each row
independently using only `N` and `P` and the four fixed constants. It performs
no data reads, fitting, interpolation, ordering assumptions, or cross-row state,
as required.
