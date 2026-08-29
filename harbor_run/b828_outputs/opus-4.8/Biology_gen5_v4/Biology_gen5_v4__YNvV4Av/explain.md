# Discovered Law for `X(t, I_light_prev)`

## Formula

$$
X(t, I) = A(I)\,\sin(\omega t + \varphi)
\;+\; a_2\cos(2\omega t) + b_2\sin(2\omega t)
\;+\; b_3\sin(3\omega t)
$$

with a light-driven, **saturating (Hill) amplitude**

$$
A(I) = c + V\,\frac{I^{\,n}}{K^{\,n} + I^{\,n}}.
$$

Here `t` is time and `I = I_light_prev` is the previous light intensity.

## Fitted parameters

| symbol | meaning | value |
|--------|---------|-------|
| $\omega$ | angular frequency | `0.262367` (period $2\pi/\omega \approx 23.95$) |
| $\varphi$ | fundamental phase | `-0.018947` |
| $c$ | dark (baseline) amplitude | `0.813634` |
| $V$ | max light-induced amplitude gain | `0.792849` |
| $K$ | half-saturation light level | `0.793034` |
| $n$ | Hill coefficient | `5.19806` |
| $a_2$ | $\cos 2\omega t$ coefficient | `-0.297560` |
| $b_2$ | $\sin 2\omega t$ coefficient | `0.062544` |
| $b_3$ | $\sin 3\omega t$ coefficient | `-0.054069` |

**Fit quality:** $R^2 = 0.9833$ on the training set. The unexplained
variance is heteroscedastic noise whose magnitude grows with the signal
amplitude (residual std rises from ~0.08 at low `I` to ~0.15 at high `I`),
i.e. the deterministic law is essentially fully captured.

## Methodology

1. **Spotting the oscillation.** Sorting `X` against `t` revealed a clear
   periodic signal. A frequency scan of a linear model
   $X = c_0 + a\cos\omega t + b\sin\omega t$ located a sharp optimum at
   $\omega \approx 0.2624$, i.e. a period of ~24 (a circadian rhythm — fitting
   the biology domain).

2. **Light dependence of the amplitude.** Binning by `I` and fitting the
   fundamental in each bin showed the offset and phase are ~0 and constant,
   while the fundamental **amplitude rises with `I` and then saturates**
   (~0.79 near `I=0`, plateauing at ~1.59 for `I ≳ 1.4`). This sigmoidal
   shape is well described by a Hill function $c + V I^n/(K^n+I^n)$.

3. **Waveform harmonics.** Residual analysis exposed strong, **light-
   independent** 2nd- and 3rd-harmonic components (at $2\omega$ and $3\omega$).
   Allowing them to depend on `I` yielded coefficients ~0, confirming they are
   fixed features of the waveform. Biologically: `I_light_prev` amplifies the
   fundamental circadian component (saturating), while the fixed harmonics set
   the intrinsic non-sinusoidal shape of the rhythm.

4. **Joint nonlinear fit.** All parameters were then fit simultaneously with
   `scipy.optimize.curve_fit`. Harmonics beyond the 3rd and any residual
   `I`-interaction terms were verified to be negligible (amplitudes < 0.007),
   so the model was capped at three harmonics.

## Extrapolation notes

- The `t` dependence is a truncated Fourier series (strictly periodic), so it
  extrapolates safely to any time.
- The `I` dependence uses a **saturating** Hill term rather than a linear one,
  so predictions remain bounded and physically sensible for `I` beyond the
  training range.
