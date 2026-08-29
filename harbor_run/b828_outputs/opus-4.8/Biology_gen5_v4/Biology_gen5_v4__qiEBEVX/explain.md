# Discovered Law for `X(t, I_light_prev)`

## Formula

$$
X(t, I) = C + e^{-\lambda t}\Big[\big(A_1 + B_1\tanh(kI)\big)\cos(\omega t + \varphi_1)
+ C_2\cos(2\omega t + \varphi_2) + C_3\cos(3\omega t + \varphi_3)\Big]
$$

where $I \equiv$ `I_light_prev`.

### Fitted parameters

| symbol | value | meaning |
|--------|-------|---------|
| $C$        | -0.00559 | baseline offset |
| $\lambda$  | 0.004964 | slow amplitude decay rate |
| $\omega$   | 0.26235  | angular frequency (period $2\pi/\omega \approx 23.95$) |
| $k$        | 0.67710  | light-saturation constant |
| $A_1$      | 0.76977  | dark-limit fundamental amplitude |
| $B_1$      | 1.48679  | light-driven fundamental amplitude |
| $\varphi_1$| -1.59340 | fundamental phase |
| $C_2$      | -0.37115 | 2nd-harmonic amplitude |
| $\varphi_2$| 0.18833  | 2nd-harmonic phase |
| $C_3$      | 0.06289  | 3rd-harmonic amplitude |
| $\varphi_3$| 1.45319  | 3rd-harmonic phase |

**Fit quality on training data:** $R^2 = 0.9958$, RMSE $= 0.063$.

## Methodology

1. **Exploration.** Binning `X` by `t` revealed a clear oscillation with a
   period of ~24 (a circadian rhythm, consistent with the biology domain). The
   peak amplitude slowly shrank with `t` (2.28 → 1.62 across the range),
   indicating a slow exponential decay of the envelope.

2. **Light dependence.** Within a narrow `t` slice near a peak, `X` rose
   monotonically with `I_light_prev` and then *saturated* for `I > ~1.2`. A
   saturating function (`tanh`) of `I` modulating the oscillation amplitude
   captured this; a plain linear term did not.

3. **Non-sinusoidal shape.** A single cosine reached only $R^2 = 0.94$.
   Residuals plotted against phase (`t mod 24`) showed a systematic pattern at
   *twice* the base frequency, revealing harmonics. Adding a 2nd harmonic lifted
   $R^2$ to 0.992 and a 3rd to 0.996; a 4th gave no further gain, so the
   waveform is well described by three Fourier modes.

4. **Where light enters.** Allowing each harmonic its own `I`-dependence showed
   that only the *fundamental* amplitude is light-modulated; the 2nd/3rd
   harmonics have essentially constant amplitude. The model was simplified
   accordingly with no loss of accuracy.

5. **Fitting.** All parameters were fit simultaneously with
   `scipy.optimize.curve_fit` (Levenberg–Marquardt) on the full training set.

## Interpretation

The system is a **decaying, light-entrained circadian oscillator**: a ~24-period
rhythm whose (non-sinusoidal) amplitude is set by the previous light input `I`
through a saturating response, riding on a slowly relaxing envelope in time.
