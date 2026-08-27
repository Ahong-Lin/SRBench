# Discovering the law for `dv_dt` (braking-cart dynamical system)

## Summary of the discovered law

```
dv_dt = v * ( a + b·bt + A·sin(k·x) + B·cos(k·x) )
```

with `v = v`, `bt = brake_temperature`, `x = cart_position`, and fitted constants

| constant | value        | role |
|----------|--------------|------|
| `a`      | −0.0658405   | speed-proportional braking / drag deceleration |
| `b`      | +0.000163466 | brake **fade**: deceleration weakens as the brake heats |
| `A`      | −0.0147308   | amplitude (×v) of a position-periodic force, sine part |
| `B`      | +0.00368581  | position-periodic force, cosine part |
| `k`      | 0.109        | spatial angular frequency (wavelength ≈ 2π/k ≈ 58) |

Equivalently

```
dv_dt = −v·(0.0658 − 0.0001635·bt)          # braking with thermal fade
        − v·0.01518·sin(0.109·x + 2.897)     # position-periodic force, amplitude ∝ v
```

All predicted accelerations are negative (the cart always decelerates), and `dv_dt → 0`
as `v → 0`, which is physically correct.

## Methodology

1. **Data reconnaissance.** The trajectory is a single time series (`t ∈ [0, 27]`, 4500 rows).
   `v` decreases **monotonically** (20 → 3.9), `x = ∫v dt` increases monotonically, and
   `brake_temperature` rises to ≈62 and then **falls back to ≈51** (a "fold"). Because
   `dv_dt < 0` everywhere, `v`, `t`, `x` are all one-to-one with each other; only `bt`
   provides an independent (folded) signal. This near-collinearity is the central difficulty.

2. **The companion ODE is exactly recoverable.** As a cross-check I fit the finite-difference
   `d(bt)/dt` and found a clean, exact relation
   ```
   d(brake_temperature)/dt = 2 + 0.5·v − 0.1·bt      (R² ≈ 1.0)
   ```
   i.e. Newtonian heating ∝ v and cooling toward ambient (bt* = 20). This confirmed the
   generator uses clean coefficients and that `bt` is a genuine, smooth second state variable.

3. **Structure of `dv_dt`.** `dv_dt` is **not monotonic** in `t`/`v`; it oscillates several
   times. Since `v`, `t`, `x` are monotonic, an oscillation implies a genuine periodic
   dependence on a third quantity. Analysis of the extrema (constant spacing Δx ≈ 32–39,
   cumulative-phase-vs-`x` regression R² ≈ 0.995) showed the oscillation is **periodic in
   cart position** `x`. The oscillation **amplitude scales with `v`** (peak-to-peak ∝ v):
   including only a `v·sin(kx)` / `v·cos(kx)` term (rather than a constant- or v²-amplitude
   term) is what extrapolates.

4. **The smooth part is a fading brake.** Removing the oscillation, the trend is well described
   by `dv_dt = −v·(a + b·bt)` with `b > 0` (deceleration decreases as the brake heats — brake
   fade). Higher-order polynomial fits in `(v, bt)` reach very high in-sample R² (≈0.99) but
   are pure over-fitting of the collinear trajectory.

5. **Model selection by extrapolation.** Because the scored test set is the *right-hand time
   segment*, I selected the model with a **time-ordered hold-out** (train on the first 80 %,
   score the last 20 %) rather than in-sample R². Results were decisive:
   * High-degree `(v,bt)` polynomials: in-sample R² up to 0.997 but hold-out RMSE 0.9–1.4
     (catastrophic blow-up).
   * `dv_dt = −v·(a+b·bt)` (no oscillation): hold-out RMSE ≈ 0.038.
   * `dv_dt = v·(a + b·bt + A·sin kx + B·cos kx)` with amplitude ∝ v: hold-out RMSE ≈ **0.021**.

   The oscillation's local wavelength shrinks slightly along the run; the value `k ≈ 0.109`
   (wavelength ≈ 58) is the local frequency in the *late* part of the trajectory and gives the
   best extrapolation into the (later-time) test regime. Adding a 2nd spatial harmonic, a
   constant-amplitude sinusoid, or a `v²` amplitude all *raised* in-sample R² but *hurt*
   hold-out accuracy, so they were rejected.

## Final fit

Coefficients above are least-squares fits of `dv_dt` on the **full** training set with the
feature set `[v, v·bt, v·sin(0.109x), v·cos(0.109x)]`.

* In-sample R² ≈ 0.79 (the residual is the part of the position-oscillation whose frequency
  drifts and which cannot be captured without over-fitting).
* Time-ordered hold-out (last 20 %) RMSE ≈ 0.020, versus a naive-mean baseline std ≈ 0.05.

## Caveats

* `v`, `t`, `x` are collinear along one trajectory, so the split of the smooth deceleration
  between "drag ∝ v" and "temperature fade ∝ v·bt" is only weakly identified (it relies on the
  `bt` fold). The functional *form* was chosen for physical plausibility and for stable
  extrapolation, not because the coefficients are uniquely determined.
* The periodic force's spatial frequency appears to increase slightly as the cart slows;
  `k = 0.109` is tuned to the end of the observed window (closest to the extrapolation target).
  The oscillation amplitude ∝ v is small at the low speeds reached in the test segment, so
  residual phase error there has limited impact.
