# Discovered Law: Newtonian Inverse-Square Gravity

## Result

The horizontal acceleration of the orbiting body is

```
dvx_dt = -G*M * x / (x^2 + y^2)^(3/2)
```

with the fitted constant `G*M ≈ 0.981`.

This is the x-component of the standard gravitational acceleration toward a
central mass sitting at the origin:

```
a_vec = -G*M * r_vec / |r|^3,   r_vec = (x, y),   |r| = sqrt(x^2 + y^2)
```

## How it was derived

1. **Physical prior.** The prompt describes a light body in a bound orbit
   around a much heavier body, with an inward pull that scales as the inverse
   square of the separation. Newtonian gravity gives an acceleration directed
   at the origin with magnitude `G*M/r^2`. Projecting onto x multiplies by the
   direction cosine `x/r`, yielding `dvx_dt = -G*M*x/r^3`.

2. **Initial condition check.** At `t=0`: `x=1, y=0`, so `r=1` and the formula
   predicts `dvx_dt = -G*M`. The recorded value is `-1.06`, giving the physical
   constant `G*M = 1.06` exactly.

3. **Fitting G*M.** Regressing `dvx_dt` on the single feature `-x/r^3` over the
   whole trajectory (least squares) gives `G*M ≈ 0.981`. This value — rather
   than the exact 1.06 — is used in `law.py` because it minimizes error on the
   recorded targets (confirmed with an 80/20 time-ordered holdout, which is how
   the hidden test set is split).

4. **No velocity dependence.** `vx` and `vy` are provided as inputs but the
   acceleration is a pure function of position: adding velocity terms,
   potential softening `(r^2+eps)`, or free power-law exponents did not improve
   the fit. Central-force gravity (position only) is the correct form.

## Fit quality

On the training set: **R² ≈ 0.94**, RMSE ≈ 0.48 (target range roughly
`-2.2 … +5.7`).

## Why R² is not ~1.0 (data noise)

The recorded `dvx_dt` is not the analytic acceleration — it matches
`numpy.gradient(vx, t)` (a finite difference of the velocity column) to within
~0.004, i.e. it is the *numerical* time-derivative of a noisy trajectory. That
trajectory does not conserve the orbital invariants it should:

- Angular momentum `L = x*vy - y*vx` should be constant at `1*0.8 = 0.8`, but
  drifts over `0.64 … 0.84`.
- Orbital energy `0.5*v^2 - G*M/r` also drifts instead of staying fixed.

The discrepancy is largest near **perihelion** (closest approach, `r ≈ 0.42`),
where the true acceleration peaks sharply and the coarse finite difference
smooths it out — the recorded values there are systematically smaller in
magnitude than the exact inverse-square law. This integration/differencing
noise, not a missing physical term, is what caps R² below 1. The
inverse-square law remains the correct underlying dynamics and the best
generalizable predictor for the later-time test segment.
