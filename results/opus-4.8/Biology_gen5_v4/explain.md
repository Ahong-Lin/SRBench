# Discovered Law

## Formula

The output `X` is a **light-entrained damped circadian oscillator**. It is a decaying
oscillation with a fundamental period of ≈ 24 (a circadian clock), whose fundamental
amplitude is controlled by the previous light intensity `I_light_prev` through a
saturating (Hill/sigmoid) response, plus small 2nd and 3rd harmonics that give the
limit cycle its non-sinusoidal shape:

```
A(I) = a + s · I^n / (K^n + I^n)                     (light-dependent amplitude)

X(t, I) = e^(−g·t) · [ A(I)·sin(w·t) + B·cos(w·t)
                       + C2·sin(2·w·t) + D2·cos(2·w·t)
                       + C3·sin(3·w·t) + D3·cos(3·w·t) ]
```

where `t` is time and `I = I_light_prev`.

## Fitted parameters

| Symbol | Meaning | Value |
|--------|---------|-------|
| `w`  | angular frequency | 0.26234  (period 2π/w ≈ **23.95**) |
| `g`  | damping / decay rate | 0.00494 |
| `a`  | baseline amplitude (dark limit) | 0.99907 |
| `s`  | light-driven amplitude gain | 0.98853 |
| `K`  | half-saturation light level | 0.80970 |
| `n`  | Hill coefficient (steepness) | 4.90284 |
| `B`  | fundamental cosine term | −0.03440 |
| `C2`, `D2` | 2nd-harmonic sin / cos | 0.07231, −0.36244 |
| `C3`, `D3` | 3rd-harmonic sin / cos | −0.06309, 0.00744 |

So the amplitude rises from ≈ 1.0 in the dark (I → 0) to ≈ 2.0 in bright light
(I → 2), with a sharp switch near `I ≈ 0.81`.

## Methodology

1. **Exploration.** `X` showed no linear correlation with either input. Slicing the
   data into narrow `I_light_prev` bands and sorting by `t` revealed a clean
   oscillation whose peaks slowly shrank over time — a **damped oscillation** with a
   period of ≈ 24 (strongly suggestive of a circadian rhythm, matching the biology
   context).

2. **Fundamental fit.** Fitting `C + A·e^(−g·t)·sin(w·t+φ)` to each band gave a
   consistent `w ≈ 0.2624` (period ≈ 24), `g ≈ 0.005`, `φ ≈ 0`, `C ≈ 0`, while the
   amplitude `A` clearly grew with `I`.

3. **Amplitude law A(I).** Extracting the least-squares amplitude in fine `I` bins
   traced out a sigmoid: a low plateau ≈ 1.0 for small `I`, a steep rise near
   `I ≈ 0.8`, and a high plateau ≈ 2.0. A **Hill function** fit this precisely
   (`a=1.0, s=0.99, K=0.81, n≈4.9`).

4. **Harmonics.** The residuals of the single-sinusoid model were *smooth* (very low
   within-bin scatter), not noise, and oscillated at twice and three times the
   fundamental frequency — the signature of a nonlinear limit cycle. Adding 2nd and
   3rd harmonic terms (sharing the same decay envelope) raised the fit from
   R² ≈ 0.95 to **R² ≈ 0.999**. A 4th/5th harmonic added nothing, so the series was
   truncated at 3 harmonics.

5. **Joint fit.** All parameters were finally optimized simultaneously with
   `scipy.optimize.curve_fit`.

## Fit quality

On the training data: **R² = 0.9987**, **RMSE ≈ 0.035** (signal amplitude ≈ 1–2).

Because the model is a product of a physically-motivated exponential decay and a
periodic (Fourier) core with a well-determined period, it extrapolates smoothly to
new `t` and `I_light_prev` values.
