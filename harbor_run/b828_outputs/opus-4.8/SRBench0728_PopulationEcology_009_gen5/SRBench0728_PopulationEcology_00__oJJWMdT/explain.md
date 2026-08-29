# Discovered Law for `dN_dt`

## Summary

The target is the instantaneous right-hand side of an ODE for a population `N`
that is regulated by a `crowding_load` variable `C`. The discovered law is an
**autonomous, per-capita growth law**:

```
dN/dt = N · g(N, C)
g(N, C) = a + b·N + c·C + d·C² + e·N·C
```

with least-squares parameters fit on the full training trajectory:

| param | value            | term        |
|-------|------------------|-------------|
| a     |  5.419348e-01    | constant    |
| b     | -2.765498e-05    | N           |
| c     | -7.618398e-04    | C           |
| d     |  1.519238e-07    | C²          |
| e     |  5.650655e-08    | N·C         |

Training fit: **R² = 0.9853**, RMSE = 10.29 (over a target range of about
−139 … +299).

## Methodology

1. **Data inspection.** The trajectory is a damped oscillation: `N` overshoots
   to ~1600, `C` lags behind, and both spiral inward to an equilibrium near
   `N = C ≈ 900`. This is the signature of a growth process regulated by a
   *delayed / smoothed* load variable.

2. **Auxiliary variable identified.** Numerically differentiating `crowding_load`
   shows, to machine precision (R² > 0.999999999),

   ```
   dC/dt = 0.2 · (N − C)
   ```

   i.e. `crowding_load` is an exponentially-weighted moving average of the
   population (relaxation time τ = 5). This confirms a 2-D coupled system whose
   equilibrium is `N = C`. Growth must therefore vanish on the line `N = C`, so
   the growth law has to depend on **both** `N` and `C` (a law of the form
   `r·N·(1 − C/K)` alone cannot reproduce the observed `N`-dependence of the
   growth-nullcline and only reaches R² ≈ 0.96).

3. **Per-capita analysis.** Dividing the target by `N` gives the per-capita
   rate `g = dN/dt / N`. Binning shows `g` is dominated by an almost-linear
   decrease in `C` (a logistic-in-crowding response) with a secondary
   dependence on `N`. Fitting `g` as a low-order polynomial in `(N, C)` and
   testing many mechanistic candidates (theta-logistic, Gompertz, rational
   Holling forms, Allee, product-logistic, `(N−C)` coupling), the compact
   quadratic per-capita form above gave the best combination of global fit and
   **forward-in-time extrapolation**.

4. **Model selection by extrapolation.** Because the hidden test set is the
   later time segment (the inner part of the spiral), candidates were ranked by
   fitting on early times and predicting the innermost observed loops. The
   chosen 5-term per-capita model minimized extrapolation RMSE (≈ 4.0, versus
   ≈ 5.4 for predicting the segment mean and ≈ 11 for the plain
   `r·N·(1−C/K)`), while adding more terms (N², explicit `(N−C)` terms, or
   higher-degree polynomials) degraded extrapolation or blew up.

5. **Equilibrium check.** Setting `N = C = Nₑ` and solving `g = 0` gives
   `Nₑ ≈ 900`, matching the observed convergence point — the law reproduces the
   correct steady state without it being fit in explicitly.

## Interpretation

- `a ≈ 0.54` is the intrinsic per-capita growth rate at low load.
- The negative `c` (with the small `d`, `e` corrections) is the crowding-driven
  suppression of growth: as the load `C` builds up, per-capita growth falls and
  becomes negative, driving the population back down.
- The small `b` (self-density) and `e` (population×load) terms bend the
  growth-nullcline so that the true equilibrium sits at `N = C`, producing the
  observed damped oscillation.

## Limitations

Near the equilibrium the target is a small difference of larger terms and
carries fine structure that instantaneous `(N, C)` values resolve only
partially (local R² ≈ 0.74 there). No pointwise function of the allowed
variables removes this fully, but the chosen autonomous form is smooth,
bounded within the observed operating range, has the correct equilibrium, and
gave the best measured forward-time extrapolation.
