# Dispersal-driven spatial equilibrium: discovered law for `N_eq(c, r)`

## Summary

The equilibrium local density is well described by a **bounded logistic
(Hill-type) response in the growth rate `r`, whose half-saturation point rises
with connectivity `c`**:

```
N_eq = K / (1 + exp(-L)),          K = 100
L    = ln( N_eq / (K - N_eq) )  ≈  0.75 · ln(r) + I(c) + (small corrections)
```

Equivalently, to leading order,

```
N_eq ≈ 100 · r^0.75 / ( r^0.75 + h(c)^0.75 )
```

a Hill function of the local growth rate with exponent ≈ 3/4 and a
connectivity-dependent half-saturation `h(c)`.

* `K = 100` is a hard ceiling (carrying capacity). Every observed `N_eq` lies in
  `(0, 100)`, and the logistic form guarantees the prediction does too.
* As `r → 0` (no local growth), `N_eq → 0`: a closed dispersal network with no
  growth goes extinct. Data confirm `N_eq ∝ r^0.75` at small `r`.
* As `r → ∞`, `N_eq → 100` for every `c`.
* Increasing connectivity `c` raises the half-saturation `h(c)` (from ≈0.05 at
  `c≈0.3` up to a plateau ≈0.33 for `c ≳ 6`), so **more connected patches
  require a larger growth rate to reach the same density** — net dispersal
  drains a well-connected focal patch faster.

## How it was found

1. **Exploration.** `N_eq` grows monotonically with `r` (corr ≈ 0.82) and
   decreases with `c` (corr ≈ −0.23, strongest at small `c`). Within a fixed `c`
   slice, `N_eq` saturates toward ~100.

2. **Linearising transform.** Setting the ceiling `K = 100` and forming the
   logit `L = ln(N_eq/(100 − N_eq))`, `L` becomes almost perfectly **linear in
   `ln(r)`** within any narrow `c` band (per-band residual ≈0.015 in logit
   units). The slope is ≈ **0.75** (essentially constant once curvature is
   accounted for) and the intercept `I(c)` decreases and saturates with `c`.
   This identifies the Hill/logistic backbone with exponent ≈ 3/4.

3. **Half-saturation `h(c)`.** From the intercept, `h(c) = exp(−I(c)/0.75)`
   increases from ≈0.05 to a plateau ≈0.33 as `c` grows — a saturating,
   monotone function of connectivity.

4. **Residual structure.** A small positive curvature in `ln(r)` (concentrated
   at small `c`) and a weak `ln(c)` dependence remain. These were captured by a
   low-order polynomial expansion of `L` in the physically motivated variables

   * `x = ln(r)`            — log growth rate,
   * `u = 1/(c + 0.2)`      — regularised inverse connectivity,
   * `w = ln(c)`            — log connectivity.

   The final model regresses `L` on all monomials `x^i · u^j` with `i+j ≤ 5`,
   plus `x^i·ln(c)` and `x^i·ln(c)^2` for `i = 0,1,2` (27 coefficients).

## Implementation (`law.py`)

For each input row the function computes `x, u, w`, evaluates the fitted
polynomial `L`, and returns `N_eq = 100/(1 + e^{−L})`. The computation is
purely pointwise (no state, ordering, or data access), and the logistic link
keeps the output strictly within `(0, 100)` for any input, so the model
degrades gracefully outside the training range.

## Fit quality (training set, `N_eq`)

| metric | value |
|---|---|
| R² | 0.9999990 |
| residual std | 0.0128 |
| max abs error | 0.198 |
| max relative error | 0.66% |

For reference, the supplied `N_eq_noisy` column differs from `N_eq` with std
≈ 0.51, so the fit is well below the experimental noise level. 5-fold
cross-validation gives a held-out residual std of ≈0.016, confirming the model
generalises and is not overfitting.

## Fitted constants

* Ceiling `K = 100`.
* Dominant growth-rate exponent `≈ 0.75` (slope of `L` vs `ln r`).
* Connectivity regulariser `0.2` in `u = 1/(c+0.2)`.
* 27 polynomial coefficients (hard-coded in `law.py`, key `_COEF`).
