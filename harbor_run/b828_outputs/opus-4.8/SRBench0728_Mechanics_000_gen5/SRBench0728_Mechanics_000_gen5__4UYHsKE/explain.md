# Discovered law for `dv_dt` (braking-cart dynamical system)

## Final formula

```
dv_dt = -gamma * v  +  v^2 * g(x)

g(x) = a1*sin(K x) + b1*cos(K x)
     + a2*sin(2K x) + b2*cos(2K x)
     + a3*sin(3K x) + b3*cos(3K x)
```

with `x = cart_position` and fitted constants

| symbol | value |
|--------|-------|
| `gamma` (coeff on `v`) | `-0.0605120` (i.e. baseline term is `-0.060512 * v`) |
| `K` (spatial frequency) | `0.05329`  (wavelength `L = 2π/K ≈ 117.9`) |
| `a1, b1` | `+0.00081729, -0.00034487` |
| `a2, b2` | `-0.00121465, +0.00008102` |
| `a3, b3` | `-0.00017843, -0.00009557` |

Only `v` and `cart_position` appear. `brake_temperature` and `t` add no
independent predictive information (see below).

## Physical interpretation

The target is the acceleration of a decelerating cart:

* **`-gamma * v`** — a **linear resistance** (viscous / rolling friction).
  Critically, there is **no constant term**: the deceleration must vanish as
  `v → 0` (a cart at rest experiences no drag), and the data confirm this — the
  smooth tail of the trajectory extrapolates cleanly to zero as a straight line
  through the origin in `v`.

* **`v^2 * g(x)`** — a **quadratic (aerodynamic-type) drag whose coefficient is
  modulated periodically along the track**. This is a "washboard" road: the drag
  coefficient repeats with spatial wavelength `≈ 118` position units. Because the
  road profile is not a pure sinusoid, the first three spatial harmonics of `Kx`
  are needed. The `v^2` scaling is what makes the oscillation large at high speed
  and negligible in the slow tail.

Together these reproduce the striking qualitative feature of the data: `dv_dt`
oscillates several times early in the run (large `v`, `v^2` amplitude big) and
then settles into a smooth monotonic decay toward zero (small `v`).

## Methodology

1. **Confirmed the trajectory.** Verified that the provided `dv_dt` equals the
   numerical time-derivative of `v`, and that `d(cart_position)/dt = v`. So the
   data are one clean trajectory of an ODE system.

2. **Identified the oscillation as spatial, not temporal.** `dv_dt` oscillates
   while `v`, `brake_temperature`, and `cart_position` are all monotonic. A
   smooth function of monotonic inputs cannot oscillate — *unless* it contains a
   term like `sin(K·cart_position)`, which oscillates even though `x` is
   monotonic. The spacing between successive `dv_dt` extrema is roughly constant
   in `cart_position` (not in time), pinning the oscillation to position.

3. **Ruled out polynomial `f(v,T)`.** Polynomial fits in `v`/`brake_temperature`
   reached only R²≈0.88 in-sample and blew up catastrophically under
   extrapolation, because `v`, `T`, and a constant are strongly collinear along a
   single trajectory (large canceling coefficients that break outside the fitted
   range).

4. **Determined the baseline form by forward validation.** Fitting on the early
   segment and predicting the late segment showed a **linear `-gamma*v`** baseline
   (no constant, no `v^2`) is the only form that extrapolates; adding `v^2` or
   `v^3` to the baseline sharply worsened out-of-sample RMSE.

5. **Determined the oscillation.** After removing `-gamma*v`, the remainder is
   well described by `v^2` times a periodic function of `x`. A frequency scan
   found a fundamental `K ≈ 0.053` plus a dominant 2nd harmonic and a small 3rd
   harmonic. `K` was chosen to minimize forward-extrapolation RMSE (train on
   `t<22`, test on `t>24`), giving `K = 0.05329`.

6. **Final coefficients** were then fit by linear least squares on the **entire**
   training trajectory (best parameter estimates and phase-locking of the
   sinusoids over the full observed position range).

## Why `brake_temperature` and `t` are excluded

Adding `brake_temperature`, `t`, or their products never improved either the
in-sample fit or the forward-extrapolation error (their fitted coefficients came
out ≈0, or they degraded extrapolation via collinearity). `brake_temperature`
appears to be a *driven byproduct* of the braking (it heats up then cools) rather
than a driver of the acceleration, so it is correctly omitted from the law.

## Fit quality

* Full-trajectory: **R² = 0.899**, RMSE = 0.108.
* Forward extrapolation (train `t<22`, predict `t>24`): RMSE ≈ **0.020**
  (the tail values are small, so absolute error is what matters there).

The model is bounded and well-behaved for continued extrapolation: as `v`
decreases further, `-gamma*v → 0` and the `v^2`-scaled oscillation shrinks even
faster, matching the observed smooth approach to zero deceleration.
