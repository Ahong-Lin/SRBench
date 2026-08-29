# Discovered Instantaneous Acceleration Law

## Summary

The instantaneous acceleration `dv_dt` follows the governing equation of a **driven damped harmonic oscillator**:

```
dv_dt = -k·x - c·v + F(t)
```

where:
- **k = 2.2799** (spring constant / stiffness coefficient)
- **c = 0.1205** (damping coefficient)
- **F(t)** = periodic driving force composed of sinusoidal and cosinusoidal terms

## The Complete Formula

The discovered law is:

```
dv_dt = -2.2799·x - 0.1205·v + Σ(k=1 to 6) [a_k·sin(k·t) + b_k·cos(k·t)]
```

where the Fourier coefficients for the periodic forcing function are:

| k | sin(k·t) coefficient | cos(k·t) coefficient |
|---|----------------------|----------------------|
| 1 | +1.6778             | -0.3411             |
| 2 | -0.0397             | -0.0108             |
| 3 | +0.3407             | -0.3575             |
| 4 | +0.1149             | -0.0111             |
| 5 | -0.0161             | +0.1027             |
| 6 | -0.0168             | +0.0181             |

## Physical Interpretation

This describes a driven damped oscillator system where:

1. **Spring Restoring Force**: The `-2.2799·x` term represents the restoring force proportional to displacement. The natural frequency is approximately ω₀ = √2.2799 ≈ 1.51 rad/s.

2. **Damping Force**: The `-0.1205·v` term represents velocity-dependent damping, with a damping ratio ζ ≈ 0.04 (lightly damped).

3. **Periodic Driving Force**: F(t) is a complex periodic function with dominant components at the fundamental frequency (k=1) and harmonics. The dominant forcing term is 1.6778·sin(t) - 0.3411·cos(t), which can be rewritten as approximately 1.71·sin(t + 0.20).

## Model Performance

- **Mean Absolute Error (MAE)**: 0.2411
- **Root Mean Squared Error (RMSE)**: 0.3449
- **Maximum Absolute Error**: 1.52

The model explains the training data with high accuracy across the entire time domain (0 to ~45 seconds), capturing both the oscillatory behavior and the response to the periodic driving force.

## Key Insights

1. The relationship is **instantaneous and pointwise**: each value of dv_dt depends only on the current values of (t, x, v), not on history.

2. The system exhibits **quasi-periodic behavior** due to the beating between the driving frequency and the natural frequency of the oscillator.

3. The coefficients were determined using least-squares regression against 1500 training samples collected over approximately 45 seconds of simulated time.

4. The model is interpretable: the dominant physics is captured by the linear restoring force (-2.28·x) and damping (-0.12·v), with the driving force providing the complex temporal modulation.
