# Discovered acceleration law

## Result

The instantaneous acceleration is governed by a **periodically driven nonlinear
oscillator** with a hardening restoring force and a nonlinear (velocity-dependent)
damping term:

```
dv/dt = R(x)  -  delta * sin(v)  +  gamma * sin(t)
```

with

```
R(x)  = a1*x + a3*x^3 + a5*x^5 + a7*x^7 + a9*x^9      (odd, stiffening restoring force)
delta = 0.2994                                         (nonlinear damping amplitude)
gamma = 1.197581  (≈ 1.2)                              (drive amplitude, angular frequency = 1)

a1 = -0.791971
a3 = -0.172366
a5 = -0.568575
a7 =  0.198037
a9 = -0.026032
```

This maps each `(t, x, v)` independently to `dv_dt` and requires no history,
ordering, or interpolation.

## Accuracy on training data

| metric | value |
|--------|-------|
| R²     | 0.99998 |
| RMSE   | 0.0056 |
| max abs error | 0.018 |

## How the law was found

1. **Linear screening.** `dv_dt` is strongly (negatively) correlated with `x`
   (r ≈ −0.86) and essentially uncorrelated with `v` and `t` on their own. A
   plain linear fit `a·x + b·v + c` only reaches R² ≈ 0.74, so the relationship
   is nonlinear.

2. **Restoring force.** Replacing `x` by odd powers sharply improved the fit
   (`-x^3` alone gives R² ≈ 0.95). Isolating the pure `x`-dependence (after
   removing the drive and damping) yields a clean **odd function that is nearly
   linear near the origin (slope ≈ −0.85) and stiffens rapidly** toward the edges
   of the sampled range (`R(±1.73) ≈ ∓5.4`). This is a classic *hardening spring*.
   Its Taylor/odd-polynomial representation converges slowly, so terms up to
   `x^9` are retained; the resulting `R(x)` is smooth and monotonic across the
   whole observed range (and extrapolates monotonically just beyond it).

3. **Periodic drive.** Scanning frequencies showed a dominant sinusoidal
   forcing at **angular frequency 1**, phase 0: adding `gamma·sin(t)` lifted the
   fit from R² ≈ 0.95 to ≈ 0.998. The best-fit amplitude is `gamma ≈ 1.20`.

4. **Nonlinear damping.** The remaining velocity dependence was captured *exactly*
   by `-delta·sin(v)`: fitting the residual in powers of `v` produced coefficients
   `(-0.30·v, +0.05·v^3, -0.0025·v^5, …)` whose ratios match the Taylor series of
   `-0.30·sin(v)` to all measured orders. Adding higher `v`-powers beyond `sin(v)`
   gives no further improvement, confirming the damping is precisely `-delta·sin(v)`
   with `delta ≈ 0.30`.

5. **Validation.** 5-fold cross-validation confirms every component reduces the
   held-out error (out-of-sample RMSE tracks the in-sample RMSE with no sign of
   overfitting), and the closed-form model reproduces the data with R² = 0.99998.

## Physical interpretation

The system behaves like a mass on a **stiffening (nonlinear) spring**, subject to
a **weak velocity damping** and a **unit-frequency periodic external drive** of
amplitude ≈ 1.2 — i.e. a Duffing-type forced oscillator, generalized so that the
damping saturates like `sin(v)` and the restoring force stiffens faster than a
single cubic term.
