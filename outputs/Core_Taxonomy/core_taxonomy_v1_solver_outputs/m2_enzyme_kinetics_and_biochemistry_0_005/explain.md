# Discovered law for equilibrium bound complex `C(Lt)`

## Summary

The bound complex `C` is the physical root of a **quadratic equation in `C`**
whose coefficients are **cubic polynomials in the total ligand `Lt`**:

```
a(Lt) * C^2 + b(Lt) * C + c(Lt) = 0
C(Lt) = ( -b(Lt) - sqrt( b(Lt)^2 - 4 a(Lt) c(Lt) ) ) / ( 2 a(Lt) )   # lower root
```

with

```
a(Lt) = 1 + 0.8276830 Lt + 0.10368756 Lt^2 + 0.0018751969 Lt^3
b(Lt) = -0.7913095 - 2.4633144 Lt - 0.7940098 Lt^2 - 0.0139853 Lt^3
c(Lt) = -0.0001303 + 0.7596404 Lt + 1.2003700 Lt^2 + 0.0121121 Lt^3
```

(The `C^2` coefficient is normalized so that its constant term is `1`.)

## Why this form (biology)

This is the **generalized tight-binding / Morrison equation**. In a receptor
binding assay at fixed total receptor `Rt`, mass balance plus the equilibrium
constants relate the measured complex `C` to the *free* ligand. Eliminating the
free-ligand concentration algebraically leaves a polynomial relation between the
observable `C` and the controlled total ligand `Lt`.

- For a simple 1:1 interaction this reduces to the classic Morrison quadratic
  `C^2 - (Lt + Rt + Kd) C + Rt·Lt = 0`, i.e. coefficients **linear** in `Lt`,
  giving a monotone curve that saturates at `Rt`.
- The observed curve here is **non-monotonic**: `C` rises steeply (tight
  binding, near-stoichiometric at low ligand), peaks at `C ≈ 1.700` near
  `Lt ≈ 11`, then declines slowly (to `≈ 1.488` at `Lt = 50`). This "hook"
  behavior is the signature of a higher-order equilibrium (a second, weaker
  ligand-binding event / ligand-induced species that removes measured complex at
  high ligand). Eliminating the free ligand from such a system raises the degree
  of the coefficient polynomials — captured here by the **cubic** `a, b, c`.

The lower (`-sqrt`) root is the physical branch: it gives `C(0) ≈ 0`, `C ≥ 0`,
and reproduces both the sharp rise and the gentle high-ligand decline.

## Methodology

1. **Exploration.** Loaded `train_data.csv` (`Lt` in [0.01, 50], 4500 rows).
   Confirmed `C` is smooth and strictly unimodal: increasing up to `Lt ≈ 11`
   (`C_max = 1.70024`), then strictly decreasing. The clean `C` column is
   deterministic; the injected noise (`C_noisy`) has std ≈ 0.020.

2. **Mechanistic fits.** Pure Morrison (monotone) cannot fit (RMSE 0.075).
   Morrison×decline, substrate-inhibition, sequential two-site, and
   ligand-induced-dimerization models all plateaued at RMSE ≈ 0.002–0.005 —
   good but structurally imperfect and requiring per-point root finding.

3. **Algebraic discovery.** Searched for an implicit polynomial relation
   `P(Lt, C) = 0` via the null space of a monomial design matrix. A relation
   that is **quadratic in `C`** (degree 2) with **cubic-in-`Lt`** coefficients
   collapses the residual to machine-scale, while lower coefficient degree
   (linear→RMSE 0.075, quadratic→RMSE 0.0023) does not. Coefficients were then
   fit stably by least squares (normalizing the `C^2` constant term to 1) and
   the explicit lower-root solution was formed.

4. **Validation.** 50/50 random train/test split: train RMSE 3.14e-5,
   **test RMSE 3.67e-5** — no overfitting. On the full dataset the closed form
   gives RMSE = 3.16e-5, max abs error = 2.2e-4, **R² = 0.9999999754**, i.e.
   ~600× below the measurement noise.

## Fitted parameters

| coeff | `Lt^0` | `Lt^1` | `Lt^2` | `Lt^3` |
|-------|--------|--------|--------|--------|
| a(Lt) | 1 (fixed) | 0.8276830 | 0.10368756 | 0.0018751969 |
| b(Lt) | -0.7913095 | -2.4633144 | -0.7940098 | -0.0139854 |
| c(Lt) | -0.0001303 | 0.7596404 | 1.2003700 | 0.0121121 |

## Implementation notes

`law()` in `law.py` evaluates the three cubics for the single supplied `Lt`,
computes the discriminant (clamped at 0 to guard against tiny negative
round-off), and returns the lower root. It uses only `Lt` and the fixed fitted
constants, is fully pointwise (no state, ordering, I/O, or interpolation), and
is a closed-form algebraic expression.
