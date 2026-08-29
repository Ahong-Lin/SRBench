# Discovering the law for `dv_dt`

## Summary

The measured acceleration is reproduced (max abs error ≈ **0.0026**, RMSE ≈ **8.5e-4**
over the full 4500-point training trajectory, whose `dv_dt` spans roughly
[-1.84, 2.0]) by the explicit pointwise relation

```
dv_dt = -x - 0.5·x³            (Duffing restoring force: linear + cubic hardening)
        - z                     (coupling force to the auxiliary variable z)
        - 2·x·v²                (position-modulated velocity term)
        - (0.11998·v + 0.12513·v³ - 0.05495·v⁵ + 0.01117·v⁷)   (odd nonlinear damping in v)
```

It uses only `x`, `v`, `z`. The variables `t` and `e` are **not** needed (see below).

## How the variables relate

Before fitting `dv_dt` I established what the columns are, using accurate
finite differences of the trajectory:

- `dx/dt = v` to ~3e-7  → `x` is position, `v` is its velocity.
- `dv/dt` equals the `dv_dt` column to ~5e-6 → the target is the acceleration of `x`.
- `de/dt = v·z` **exactly** (to ~1e-6) → `e` is the running integral ∫ v·z dt
  (an accumulated "work/energy" bookkeeping variable). Because `e` is a pure
  time-integral of the other variables, it carries no independent instantaneous
  information for `dv_dt`; including it in a fit only adds ill-conditioned,
  high-magnitude terms that **hurt** out-of-sample extrapolation. It is dropped.

The trajectory is a single decaying oscillation (amplitude 1.0 → 0.62 → 0.43 →
0.29 → 0.20 over ~4.5 cycles): energy leaks steadily from the (x, v) oscillator
into `e`, i.e. the motion is effectively damped even though the idealized story
calls it "frictionless."

## Why it is not a plain function of `x`

A pure Duffing `dv/dt = f(x)` is impossible here: at `x ≈ +0.07` the data shows
`dv_dt ≈ +0.59` (anti-restoring), and at fixed `x ≈ 0.1` the target ranges from
-0.67 to +0.59. So the force genuinely depends on more than position. The extra
dependence turned out to be `z` and `v`.

## Identification procedure

1. **Turning points (v ≈ 0).** Restricting to the 28 rows with |v| < 0.005
   removes every velocity-dependent term. A 3-term fit there is essentially
   exact (max err 4.6e-4):
   `dv_dt = -1.0002·x - 0.4997·x³ - 0.9999·z`.
   This fixes the conservative + coupling part as `-x - 0.5·x³ - z` with clean,
   round coefficients.

2. **Velocity-dependent remainder.** The residual `r = dv_dt - (-x - 0.5x³ - z)`
   vanishes at `v = 0` and is almost a pure function of `v`. Its dominant piece
   is `r ≈ -2·x·v²` (the `x·v²` feature correlates with `r` at -0.95, coefficient
   fits to -2.000). Removing it leaves a small, odd-in-`v` damping term.

3. **Nonlinear damping.** The final residual is well described by an odd series
   in `v`: `-0.11998·v - 0.12513·v³ + 0.05495·v⁵ - 0.01117·v⁷`. This drives the
   max error down to 0.0026.

Fitting all coefficients **freely** returns
`x:-0.9994, x³:-0.5009, z:-1.0005, x·v²:-1.9999` — confirming the round core
values `-1, -0.5, -1, -2` are not imposed but are what the data contains.

## Robustness / extrapolation check

The hidden test set is the right-hand (later-time) continuation of the same
experiment, i.e. smaller-amplitude cycles that lie in the interior of the
explored (x, v, z) region. I validated by training on the first 60/70/80 % and
predicting the held-out tail:

| model | tail max-err (80/20) | coefficient stability |
|---|---|---|
| this model (x,x³,z,x·v²,v,v³,v⁵) | ~0.0012 | core coeffs constant to 3 dp across splits |
| generic deg-3 poly in (x,v,z), 20 terms | ~0.0017 | ok |
| any fit that includes `e` (deg ≥ 4) | 0.005–0.011 | unstable, over-fits |

The chosen model has the smallest, most stable extrapolation error and an
interpretable physical form, so it is the submitted law.

## Physical reading

- `-x - 0.5·x³`: the hardening spring — linear stiffness plus a cubic term that
  stiffens the restoring force at large stretch (the "cubic hardening" in the
  prompt), with k/m = 1 and β/m = 0.5.
- `-z`: a coupling/feedback force to the auxiliary degree of freedom `z`; the
  power it exchanges is exactly what accumulates in `e` (`de/dt = v·z`).
- `-2·x·v²`: a position-modulated, velocity-squared term (the kind produced by a
  position-dependent effective inertia).
- the odd `v`-series: weak nonlinear damping responsible for the observed decay.

## Implementation notes

`/app/law.py` implements `law(input_data)` mapping each row independently to a
single `{"dv_dt": ...}` prediction. It reads only `x`, `v`, `z` from each row,
uses fixed constants inferred above, keeps no state between calls, and performs
no interpolation, table lookup, differentiation, or data access.
