# Discovered Acceleration Law

## Summary

The observed system is a **forced Duffing-type oscillator with weak
amplitude-dependent (nonlinear) damping**. The instantaneous acceleration is
an explicit, pointwise function of the state `(x, v)` and the two supplied
forcing signals `(Fh, Fh2)`:

```
dv/dt = a1·x + a2·x³ + a3·v + a4·Fh + a5·Fh2 + a6·x²·v + a7·v³
```

with fitted parameters:

| term        | symbol | value            | interpretation                         |
|-------------|--------|------------------|----------------------------------------|
| `x`         | a1     | −0.9976597       | linear restoring force (≈ −ω², ω≈1)    |
| `x³`        | a2     | −0.0532415       | cubic (Duffing) hardening/softening    |
| `v`         | a3     | −0.0301803       | linear (viscous) damping               |
| `Fh`        | a4     | −0.1039345       | external forcing channel 1             |
| `Fh2`       | a5     | −0.0473974       | external forcing channel 2             |
| `x²·v`      | a6     | +0.0032952       | nonlinear damping (position-dependent) |
| `v³`        | a7     | −0.0106924       | nonlinear damping (velocity-dependent) |
| constant    | —      | +2.70e−05        | negligible, kept for completeness      |

Note `a1 + a2 ≈ −1.05`, which reproduces exactly the initial condition
(`x=1, v=0, Fh=Fh2=0 → dv/dt = −1.05`).

## Methodology

1. **Exploration.** `dv_dt` is almost perfectly anti-correlated with `x`
   (r ≈ −0.9997), pointing to a restoring-force oscillator. A pure linear fit
   in `(x, v, Fh, Fh2)` left a residual std of 0.0128 whose structure
   correlated strongly with `x³` (Duffing signature).

2. **Term selection.** Adding `x³` dropped the residual to 0.0035. The
   remaining residual correlated with `x²·v` (r≈0.65) and `v³` (r≈−0.31),
   the classic signatures of nonlinear amplitude-dependent damping. Including
   both reduced the residual to ≈5.5e−4.

3. **Forcing.** The supplied signals `Fh` and `Fh2` are genuinely required:
   removing them and compensating with additional `x`,`v` polynomial terms
   roughly doubled the extrapolation error (0.014 vs 0.0007). They enter
   linearly, consistent with additive external forces.

4. **Guarding against overfitting / validating extrapolation.** Because the
   hidden test set is the *right-hand time segment*, I validated by training on
   the first 75 % / 85 % / 90 % of the time series and predicting the remaining
   tail. The selected 7-term model gave a stable extrapolation RMSE of
   **6.5e−4 – 7.2e−4** (max abs error ≈ 1.3e−3) across all splits. A larger
   quadratic feature set fit the training data slightly better but *worsened*
   extrapolation, so it was rejected.

5. **Final fit.** Coefficients were re-estimated by ordinary least squares on
   the full training set (values in the table above).

## Fit quality

- Training RMSE: **5.5e−4**
- Training max abs error: **1.2e−3**
- Held-out right-hand extrapolation RMSE (75/85/90 % time splits): **≈7e−4**

## Implementation

`/app/law.py` implements the formula pointwise: each input row is mapped
independently to a single `{"dv_dt": ...}` prediction using only the declared
variables and the fixed fitted constants — no state, ordering, interpolation,
or hidden-data access.
