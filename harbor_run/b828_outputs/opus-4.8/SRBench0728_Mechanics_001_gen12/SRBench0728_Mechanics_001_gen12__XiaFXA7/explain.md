# Discovered acceleration law

## Result

The instantaneous acceleration is an explicit pointwise function of the state
`(x, v)` and the two supplied force channels `(Fh, Fh2)`:

```
dv_dt = c0 + c1*x + c3*x^3 + cv*v + cv3*v^3 + cFh*Fh + cFh2*Fh2
```

with fitted constants

| term        | symbol | value            |
|-------------|--------|------------------|
| constant    | c0     |  4.315e-05  (≈0) |
| x           | c1     | -0.997628        |
| x^3         | c3     | -0.053292        |
| v           | cv     | -0.027392        |
| v^3         | cv3    | -0.013423        |
| Fh          | cFh    | -0.103227        |
| Fh2         | cFh2   | -0.050473        |

Fit quality on the full training set: **RMSE = 6.2e-4**, max abs error = 1.5e-3.

## Physical interpretation

This is a **driven Duffing-type oscillator**:

- `c1*x + c3*x^3` — a linear plus (softening) cubic **restoring force**. The
  linear stiffness is essentially 1 (c1 ≈ -1), so the natural frequency is ~1
  rad/s, consistent with the ~6.3 s oscillation period seen in the data.
- `cv*v + cv3*v^3` — **damping** that is mostly linear with a small cubic
  correction.
- `cFh*Fh + cFh2*Fh2` — two externally supplied **force channels** that enter
  linearly. (`Fh`/`Fh2` are independent inputs; they are not well explained by
  `x`/`v`, so they carry genuine forcing information. Their coefficient ratio is
  close to 2:1.) The net forcing pumps energy in, which is why the oscillation
  amplitude slowly grows over the observed window.

## Methodology

1. Loaded `/app/data/train_data.csv` (4500 rows, t ∈ [0, 18]). Confirmed
   `v = dx/dt` numerically (correlation ≈ 1.0), i.e. this is a second-order
   mechanical system and the target `dv_dt` is the acceleration.
2. Baseline linear regression on `{x, v, Fh, Fh2}` gave RMSE ≈ 0.013. The
   residual correlated strongly with `x^3`.
3. Adding `x^3` dropped RMSE to ≈ 0.0035; adding `v^3` dropped it to ≈ 6e-4.
   Additional candidate terms (`x^5`, `x*v`, `x^2*v`, `x*v^2`, `Fh*x`, `Fh^2`,
   `sin x`, `t`) gave no meaningful improvement and were discarded to avoid
   overfitting.
4. **Extrapolation check** (the hidden test is the right-hand time segment):
   trained on the first 70% of the time series and evaluated on the last 30%.
   The 6-term model gave train RMSE 5e-4 / test RMSE 1e-3, confirming the law
   generalizes beyond the observed window (the linear-only model degraded to
   0.016 on the held-out segment). Adding `x^5` did not improve extrapolation.
5. Final coefficients fit by ordinary least squares on the full dataset.

## Implementation

`/app/law.py` implements the formula above, mapping each input row
independently to one `{"dv_dt": ...}` prediction using only the declared
variables `x, v, Fh, Fh2` and the fixed fitted constants. No ML black box,
lookup, interpolation, differentiation, or cross-row state is used.
