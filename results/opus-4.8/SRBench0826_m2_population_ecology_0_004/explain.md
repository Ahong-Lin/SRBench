# Recovered Law for `dN1_dt`

## Summary

The growth rate of species 1 is governed by a **generalized Lotka–Volterra
competition model with higher-order interaction terms**. The per‑capita growth
rate of `N1` is a quadratic function of the three observed state variables
`N1`, `N2`, `P1`:

```
dN1/dt = N1 · ( c0
                + c1·N1 + c2·N2 + c3·P1
                + c11·N1²  + c12·N1·N2 + c13·N1·P1
                + c22·N2²  + c23·N2·P1 + c33·P1² )
```

with the fitted coefficients

| term | coefficient |
|------|-------------|
| `1`      |  0.7070686 |
| `N1`     |  0.0064153 |
| `N2`     | −0.0119237 |
| `P1`     | −0.0020304 |
| `N1²`    | −9.7437e-06 |
| `N1·N2`  | −1.1429e-04 |
| `N1·P1`  | −1.2164e-04 |
| `N2²`    |  7.4833e-05 |
| `N2·P1`  | −1.2678e-04 |
| `P1²`    | −4.9220e-05 |

Fit quality on the full training trajectory: **R² = 0.99999954, RMSE = 7.2e-4**
(the output range spans roughly −1.5 … +3.7, so the residuals are ~10⁻⁴ of the
signal — effectively an exact recovery).

## How the form was discovered

1. **Data shape.** The file is a single continuous time trajectory
   (`t` from 0 → 54, 4500 rows). The provided `dN1_dt` matches a numerical
   derivative of `N1` to ~1e-6, confirming it is the true instantaneous rate,
   and the data are essentially noiseless.

2. **`dN1_dt` vanishes with `N1`.** Dividing the target by `N1` gives a clean
   *per‑capita* growth rate `g = dN1_dt / N1`. Regressing `g` on a full
   quadratic basis in `{N1, N2, P1}` reduced the residual to RMSE ≈ 3e‑5 — far
   below any structure in the data — which shows the rate is exactly
   `N1 · (quadratic)`. Equivalently, every term in `dN1_dt` carries a factor of
   `N1`; there is no additive constant or `N1`‑independent term. This is the
   hallmark of a birth/growth process that shuts off when the population is
   absent.

3. **Why more than a textbook 2‑species model.** The classic competitive
   Lotka–Volterra form `dN1/dt = r·N1·(1 − (N1 + α·N2)/K)` (linear per‑capita
   in `N1, N2` only) fits with R² ≈ 0.996 but leaves a **systematic,
   oscillatory residual** — it cannot reproduce the damped spiral seen in the
   trajectory. Adding `P1` as a genuine third interacting variable and allowing
   quadratic (higher-order / density‑dependent) interaction terms removes the
   structured residual entirely. `P1` is causal, not a decoy: it enters the
   dynamics with sizeable `N2·P1`, `N1·P1`, and `P1²` contributions.

4. **Biological reading of the terms.**
   - `c0` (≈ 0.71): intrinsic per‑capita growth rate of species 1.
   - `c1·N1`, `c11·N1²`: self‑crowding / density dependence.
   - `c2·N2`, `c3·P1`: linear mutual suppression by the competing species and
     by `P1` (both negative → competitive/interfering effect).
   - `c12`, `c13`, `c22`, `c23`, `c33`: **higher-order interactions (HOIs)** —
     the strength of one competitor's effect depends on the density of another.
     These are standard in modern competition ecology and are what produce the
     coupled, oscillatory approach to coexistence observed here.

## Fitting procedure

- Target: `g = dN1_dt / N1`; features: `1, N1, N2, P1, N1², N1·N2, N1·P1,
  N2², N2·P1, P1²` (all monomials of degree ≤ 2).
- Ordinary least squares on **all** training rows (equivalently, least squares
  on `dN1_dt` with each feature pre‑multiplied by `N1`).
- Sparsity checks (forward selection, term pruning) confirmed all ten terms are
  needed for the near‑exact fit; dropping the small `N1²`/`P1²` terms raises the
  residual by an order of magnitude.

## Generalization to the test set

The trajectory is a **damped spiral converging toward a coexistence
equilibrium** (`N1 ≈ 12–13`, `N2 ≈ 93–94`, `P1 ≈ 10.5`). Because the spiral
tightens over time, the later time segment used as the hidden test set lies
*inside* the region of `(N1, N2, P1)` space already covered by training, so the
model interpolates rather than extrapolates. Time‑ordered holdout checks
(training on the first 70–85 % and predicting the remainder) give validation
RMSE ≈ 0.007–0.03, and the coefficients used in `law.py` are estimated from the
full trajectory for the tightest possible fit.

## Files

- `law.py` — implements `law(input_data)`; coefficients are hard‑coded (no need
  to read the CSV at inference time). It computes the per‑capita quadratic and
  multiplies by `N1`.
