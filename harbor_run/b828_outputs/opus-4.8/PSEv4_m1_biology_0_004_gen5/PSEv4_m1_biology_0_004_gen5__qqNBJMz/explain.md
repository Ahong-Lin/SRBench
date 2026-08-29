# Discovered law for `X`

## Summary

`X` behaves like the output of a **lightly-damped multi-mode oscillatory system**
whose oscillatory amplitude is **linearly modulated by the light input**
`I_light_prev`. The relationship is an explicit, pointwise function of the two
inputs `t` and `I_light_prev`:

```
X(t, I) = D + (1 + k·I) · [ A_dc·e^(−g0·t)
                            + e^(−g1·t)·(c1·cos(w1·t) + s1·sin(w1·t))
                            + e^(−g2·t)·(c2·cos(w2·t) + s2·sin(w2·t))
                            + e^(−g3·t)·(c3·cos(w3·t) + s3·sin(w3·t)) ]
```

where `I = I_light_prev`.

## How it was found

1. A local regression of `X` on `I` in narrow `t`-windows showed that both the
   offset **and** the `I`-slope oscillate in phase and decay together. This
   revealed the multiplicative light coupling `(1 + k·I)` (slope ≈ `k`·offset,
   `k ≈ 0.09`) rather than an additive one.
2. Dividing out `(1 + k·I)` and running an iterative periodogram (matching
   pursuit) on the `t`-signal exposed three distinct angular frequencies plus a
   slow non-oscillatory relaxation.
3. Each component was assigned its own exponential damping rate and the whole
   model was refined with a global non-linear least-squares fit (inner linear
   solve for the amplitudes, outer optimisation of frequencies, dampings and
   `k`).
4. `I_light_prev` was verified to be an independent random input (no
   dependence on `t`), so the oscillations are genuinely functions of `t`.

## The three modes

| Mode | Angular freq `w` | Period (in `t`) | Damping (time-const `1/g`) | Character |
|------|------------------|-----------------|----------------------------|-----------|
| slow offset | 0 | — | `1/g0 ≈ 117` | slowly relaxing baseline |
| mode 1 | `w1 ≈ 0.2566` | ≈ 24.5 | `1/g1 ≈ 30.5` | damped, dominant transient |
| mode 2 | `w2 ≈ 1.2403` | ≈ 5.07 | `1/g2 ≈ 1.9e4` (≈ sustained) | persistent fast ripple |
| mode 3 | `w3 ≈ 0.5170` | ≈ 12.15 | `1/g3 ≈ 743` (≈ sustained) | persistent |

The dominant mode 1 (period ≈ 24.5) is a strong decaying oscillation that
dominates for small `t`; modes 2 and 3 are essentially undamped and remain
visible at large `t` once mode 1 has decayed. Note `w3 ≈ 2·w1`, i.e. mode 3 sits
near the second harmonic of the dominant oscillation.

## Fitted parameters

```
k   =  0.086553      (light-coupling coefficient)

g0  =  0.0085258     w1 =  0.2565590
g1  =  0.0327471     w2 =  1.2403367
g2  =  5.15788e-05   w3 =  0.5169836
g3  =  0.0013461

D     = -0.041167    (equilibrium, uncoupled)
A_dc  =  0.187318
c1, s1 =  1.434986,  1.357092
c2, s2 = -0.215007, -0.103850
c3, s3 =  0.117937,  0.100645
```

## Accuracy

On the training data the formula gives:

- RMSE ≈ **0.020**
- MAE  ≈ **0.015**
- max abs error ≈ 0.12

An 80/20 train/test split gives essentially equal train (0.0208) and test
(0.0215) RMSE, indicating the ~0.02 residual is measurement noise rather than
unmodelled structure — the deterministic law has been captured. `X` itself spans
roughly `[−1.4, 2.6]`, so the residual is ~1% of the range.

## Implementation

`law.py` implements the formula above verbatim as a pure pointwise function of
`(t, I_light_prev)`, mapping each input row independently to one `X`. It uses no
state, no data reads, and no ordering assumptions.
