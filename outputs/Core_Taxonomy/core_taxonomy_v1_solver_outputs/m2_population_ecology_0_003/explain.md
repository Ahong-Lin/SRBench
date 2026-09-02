# Discovered Law: Generalized Holling Type III Functional Response

## Formula

$$ f(N) = \frac{a\,N^2}{1 + b\,N + c\,N^2} $$

with fitted parameters:

| Parameter | Value | Std. error |
|-----------|-------|-----------|
| `a` | 1.006989 | 1.2e-04 |
| `b` | 1.074049 | 1.9e-04 |
| `c` | 0.704153 | 8.2e-05 |

## Fit quality (training data, 4500 rows)

- RMSE = 1.77e-04
- Max absolute error = 5.05e-04
- R² = 0.9999996

## Reasoning / methodology

The dataset gives per-predator instantaneous feeding rate `f` versus prey
density `N ∈ [0, 20]`. Two diagnostic observations drive the model:

1. **Low-density behavior.** Near `N = 0`, `f / N²` ≈ 1.0 (0.996, 0.991, …),
   i.e. `f ≈ N²`. The intake accelerates *quadratically*, not linearly. This
   rules out a Holling Type II (`f ≈ aN` at low density) and points to a
   **Type III (sigmoidal)** response, where the attack rate itself rises with
   prey availability (e.g. via predator learning / prey-switching).

2. **High-density behavior.** `f` levels off toward a plateau (~1.32),
   the signature of handling-time saturation.

The classic Type III form `f = aN²/(1 + a h N²)` captures both limits but fits
poorly here (RMSE 0.041, max err 0.11), because the observed curve also carries
a **linear handling term in the denominator**. The generalized rational form

$$ f = \frac{aN^2}{1 + bN + cN^2} $$

— the Real (1977) generalization of the Holling disc equation with a
density-dependent attack rate — captures all regimes essentially exactly.

Interpretation of the limits:
- `N → 0`: `f → a N²` with `a ≈ 1.01` (the accelerating Type III onset).
- `N → ∞`: `f → a/c ≈ 1.430` (asymptotic saturation ceiling set by handling).
- The `bN` term is a linear handling/interference correction that shapes the
  transition between the two regimes.

Parameters were obtained by nonlinear least squares (`scipy.optimize.curve_fit`)
on all 4500 `(N, f)` pairs. The extremely tight standard errors and R² confirm
the functional form is correct rather than overfit.

## Implementation

`/app/law.py` evaluates the closed form pointwise for each input row using the
three fitted constants above. No data access, state, or ordering is used.
