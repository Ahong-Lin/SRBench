# Discovered law for `X`

## Summary

The dataset behaves like a **light-driven, damped circadian oscillator** that
starts with a large-amplitude transient and relaxes toward a small, steady
rhythm. `X` is an explicit **pointwise** function of the two inputs `t` (time)
and `I_light_prev` (previous light input):

```
X(t, I) = off
        + D1 · e^(−gd·t)                                     (slow mean relaxation)
        + e^(−g1·t) ·(a1 ·cos w1 t + b1 ·sin w1 t)           (circadian transient, ~24.6)
        + e^(−g1b·t)·(a1b·cos w1b t + b1b·sin w1b t)         (2nd circadian mode, envelope shaping)
        + e^(−gh·t) ·(h1 ·cos wh t + h2 ·sin wh t)           (~12 harmonic, nearly persistent)
        + (a2·cos w2 t + b2·sin w2 t)                        (persistent ultradian, ~5.07)
        + I · e^(−g3·t) ·(c1·cos w1 t + c2·sin w1 t)         (light coupling, decaying)
```

where each angular frequency is `w = 2π / T`.

## How the structure was found

1. **`X` vs `t`.** Coarse sampling suggested a slow (~24) oscillation, but a
   high-resolution FFT of the (near noise-free) signal revealed the true
   spectrum: sharp peaks at periods **≈ 24.7**, **≈ 12.0** and **≈ 5.07**.
2. **Amplitude decay.** The point-to-point roughness and the ~24.6 component
   decay roughly exponentially (rate ≈ 0.035), while the ~12 and ~5.07
   components persist to the end of the record — a transient-plus-limit-cycle
   picture.
3. **Role of `I_light_prev`.** A local regression of `X` on `I` in short time
   windows gave a *slope* (light gain) that is a **decaying ~24-periodic
   oscillation** (amplitude ≈ 0.22 at `t=0`, → 0 by `t≈100`) and an *intercept*
   (the baseline) carrying all the oscillatory structure above. Hence
   `X = baseline(t) + gain(t)·I_light_prev`, with `gain(t)` a single decaying
   circadian mode. The instantaneous, non-lagged dependence on `I` is therefore
   real but small and vanishes at late times (late-time `X` is a smooth function
   of `t` alone).
4. **Fit.** Combining these components in a single nonlinear least-squares fit
   over all 4500 rows reproduces the data with **RMSE ≈ 0.008**, **max abs
   error ≈ 0.05**, **R² ≈ 0.9998**. An 80/20 train/test split gives the same
   test error (≈ 0.0084), confirming the form is not overfit. The residual has
   no remaining light dependence and only tiny power near the 12-period skirt.

## Fitted parameters

| symbol | meaning | value |
|---|---|---|
| `off` | constant offset | −0.02772 |
| `D1`, `gd` | slow mean relaxation amp / rate | 0.21223 / 0.010911 |
| `a1`, `b1`, `g1`, `T1` | circadian transient A (cos, sin, decay, period) | 1.73827 / 1.49644 / 0.036353 / 24.5734 |
| `a1b`, `b1b`, `g1b`, `T1b` | circadian transient B (envelope shaping) | −0.41359 / −0.27105 / 0.094412 / 23.5191 |
| `h1`, `h2`, `gh`, `TH` | ~12 harmonic | 0.13166 / 0.11976 / 0.0018802 / 12.1464 |
| `a2`, `b2`, `T2` | persistent ultradian (decay ≈ 0) | −0.23376 / −0.11149 / 5.06592 |
| `c1`, `c2`, `g3` | light coupling (at circadian frequency `w1`, decay) | 0.16681 / 0.14882 / 0.034921 |

Notes:
- `T1 ≈ 24.6` and `T1b ≈ 23.5` are two close, differently-damped circadian
  modes; together they represent a single ~24.6-period rhythm whose amplitude
  envelope is not a pure single exponential (the amplitude of a relaxing
  limit-cycle oscillator decays non-exponentially). `TH ≈ 12.1 ≈ T1/2` is its
  harmonic.
- `T2 ≈ 5.07` is an independent, essentially undamped (persistent) ultradian
  oscillation.
- The light term couples at the circadian frequency and decays away, so light
  perturbs `X` strongly early and negligibly late.

## Implementation

`law.py` hard-codes these constants and evaluates the closed-form expression for
each input row independently (no state, no data access, no interpolation),
returning `[{"X": value}]`.
