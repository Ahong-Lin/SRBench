# Discovered Mathematical Relationship

## Summary

The dataset contains samples from a dynamical system where `dx_dt` (the rate of change of `x` with respect to time) follows a **Fourier series** representation as a function of time `t`.

## Formula

The discovered law is:

```
dx_dt(t) = 0.424353·sin(t) + 1.242299·cos(t)
         - 0.075346·sin(2t) + 0.058544·cos(2t)
         - 0.170603·sin(3t) - 0.157257·cos(3t)
```

This is a **trigonometric polynomial** using three harmonics (Fourier series with fundamental frequency and its first two overtones).

## Analysis Method

1. **Initial Observation**: The dataset showed that `dx_dt` is identical to the column `v` (correlation = 1.0).

2. **Fourier Decomposition**: The velocity `v` was decomposed into its Fourier components:
   - The first harmonic can be written as: `1.313·cos(t - 0.329)`
   - Second and third harmonics provide corrections for better accuracy

3. **Harmonic Contributions**:
   - **1st harmonic** (t, 2t frequency): Dominant terms with amplitudes ~1.24 (cos) and ~0.42 (sin)
   - **2nd harmonic** (2t frequency): Moderate correction with amplitude ~0.08
   - **3rd harmonic** (3t frequency): Additional refinement with amplitude ~0.17

## Verification

The three-harmonic formula achieves:
- **MSE (Mean Squared Error)**: ~0.140 on the training dataset
- **Max Error**: ~1.3 on training data

The simpler two-harmonic formula gives MSE ~0.168.

## Physical Interpretation

This represents a **driven oscillatory system**, where:
- The primary motion follows a cosine pattern with slight phase shift
- Secondary oscillations at double and triple frequencies represent higher-order effects or nonlinearities in the system

The formula can also be understood as the solution to a differential equation of the form:
```
d²x/dt² + ω²x = forcing_function(t)
```

where the particular solution dominates the observed behavior.

## Parameters

- **Amplitude (1st harmonic)**: R = √(0.424353² + 1.242299²) ≈ 1.313
- **Phase (1st harmonic)**: φ = arctan2(1.242299, 0.424353) ≈ 1.242 rad ≈ 71.2°
- **Relative Error**: < 1.3 units across full range

## Coefficients Used

| Harmonic | sin(nt) coefficient | cos(nt) coefficient |
|----------|-------------------|-------------------|
| n=1      | 0.424353          | 1.242299          |
| n=2      | -0.075346         | 0.058544          |
| n=3      | -0.170603         | -0.157257         |

These coefficients were obtained by least-squares fitting to the training data.
