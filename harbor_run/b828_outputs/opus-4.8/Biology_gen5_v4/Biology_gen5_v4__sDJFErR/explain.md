# Discovered Law for `X`

## Summary

The data describe a **damped, light-driven circadian oscillator**. `X` is a
non-sinusoidal oscillation in time `t` with a period of ~24, whose amplitude
increases with the previous light intensity `I_light_prev` and slowly decays
over time.

## Formula

$$
X(t, I) = e^{-t/\tau}\,\big[(a + b\,I)\sin(\omega t) + c\cos(\omega t)\big]
\; + \; d\cos(2\omega t) + e\sin(2\omega t) + g\sin(3\omega t) + f
$$

where `I = I_light_prev`.

## Fitted parameters (R² ≈ 0.994 on training data)

| Parameter | Value | Meaning |
|-----------|-------|---------|
| ω (omega) | 0.262226 | angular frequency → period 2π/ω ≈ 23.96 (circadian ~24) |
| a | 0.928806 | base amplitude of the fundamental |
| b | 0.666477 | light-intensity gain on the amplitude |
| c | −0.033829 | small cosine (phase) component of the fundamental |
| τ (tau) | 182.47 | amplitude decay time constant |
| d | −0.301062 | 2nd-harmonic cosine amplitude |
| e | 0.060654 | 2nd-harmonic sine amplitude |
| g | −0.048471 | 3rd-harmonic sine amplitude |
| f | −0.006307 | constant offset |

## Methodology

1. **Exploration.** Sorting the data by `t` revealed a clear oscillation with a
   period near 24. A frequency scan (fitting `1, cos(ωt), sin(ωt)` and maximizing
   R²) pinned the fundamental at ω ≈ 0.262 (period ≈ 23.9), consistent with a
   biological circadian rhythm.

2. **Light dependence.** At fixed `t`, larger `I_light_prev` produced larger `X`.
   Adding interaction terms `I·sin(ωt)` and `I·cos(ωt)` showed the effect of light
   is essentially an **amplitude gain on the fundamental** (`a + b·I`); the
   `I·sin(ωt)` coefficient (~0.53–0.67) was strongly significant while a direct
   additive `I` term and light-modulation of the harmonics were negligible.

3. **Amplitude decay.** Residuals of the pure sinusoid correlated with `t·sin(ωt)`,
   indicating a shrinking amplitude. A single exponential envelope `exp(-t/τ)`
   (τ ≈ 182) captured this cleanly, lifting R² from ~0.93 to ~0.99.

4. **Waveform shape (harmonics).** Residuals then showed structure at `2ω` and
   `3ω`. Adding constant 2nd- and 3rd-harmonic terms captured the non-sinusoidal
   shape of the limit cycle. Notably the constant term `d·cos(2ωt)+f ≈ −0.31` at
   `t=0` matches the observed `X(0) ≈ −0.29`. Harmonics beyond the third gave no
   meaningful improvement.

5. **Fitting.** Final coefficients were obtained by nonlinear least squares
   (`scipy.optimize.curve_fit`) over all parameters simultaneously, reaching
   R² ≈ 0.994 with RMSE ≈ 0.074.

## Interpretation

`X` behaves like the output of a self-sustaining (circadian) oscillator: a
fundamental ~24-unit rhythm whose strength is set by the prior light input,
riding on a slowly relaxing amplitude and with a mildly anharmonic waveform
represented by the second and third harmonics.
