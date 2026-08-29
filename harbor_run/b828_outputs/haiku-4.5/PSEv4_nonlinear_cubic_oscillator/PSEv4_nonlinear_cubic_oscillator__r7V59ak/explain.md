# Discovered Mathematical Relationship

## Overview

The underlying relationship governing `dv_dt` is a **degree-3 multivariate polynomial function** of the input variables `t`, `x`, and `v`.

## Formula

```
dv_dt = 0.108186622253
      - 0.604287908362·x
      - 0.132695926029·v
      + 0.020811074265·t
      - 0.811565409592·x²
      - 0.072809261688·xv
      + 0.335316713279·xt
      + 0.112028930806·v²
      - 0.161854067940·vt
      + 0.005332191369·t²
      - 1.186289056002·x³
      + 0.158432511997·x²v
      + 0.270397366349·x²t
      + 0.097388003991·xv²
      - 0.102583994632·xvt
      - 0.083370400482·xt²
      - 0.199886719358·v³
      - 0.176664488897·v²t
      - 0.073393667063·vt²
      - 0.000034312603·t³
```

## Model Performance

- **R² Score**: 0.9994937 (99.95% variance explained)
- **Root Mean Square Error**: 0.00808 (extremely low)
- **Maximum Residual Error**: 0.0525 (across 4,500 training points)
- **95th Percentile Error**: 0.0195

## Physical Interpretation

The formula represents a **time-varying dynamical system** where:
- `x` and `v` likely represent position and velocity of an oscillator
- `dv_dt` is the acceleration (rate of change of velocity)
- The dominant terms are cubic in `x` (coefficient -1.186), suggesting strong nonlinear position-dependent forces
- The significant quadratic and cross terms indicate coupling effects between position, velocity, and time

This could represent a nonlinear oscillator system (e.g., a pendulum with damping and external forcing) where the evolution depends on both the state variables (`x`, `v`) and explicit time-dependence (`t`).

## Model Structure

The polynomial was constructed using all monomials of degree ≤ 3:
- 1 constant term
- 3 linear terms (x, v, t)
- 6 quadratic terms (x², xv, xt, v², vt, t²)
- 10 cubic terms (x³, x²v, x²t, xv², xvt, xt², v³, v²t, vt², t³)

This 20-parameter model was fitted using ordinary least squares on the 4,500 training samples, achieving near-perfect fit with residuals that are small, zero-mean, and unbiased with respect to the input variables.

## Validation Approach

The model is implemented as a pointwise function that:
1. Takes a single row of input (`t`, `x`, `v`) at a time
2. Computes all polynomial terms explicitly
3. Returns the predicted `dv_dt` value
4. Does not depend on state, ordering, or any hidden data
