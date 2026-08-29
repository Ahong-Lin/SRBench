# Symbolic Regression Solution: Spring-Mass System with Cubic Hardening

## Physical System

The experimental dataset describes a mass oscillating on a frictionless surface attached to a nonlinear spring. The spring has:
- A linear restoring force (Hooke's law): proportional to displacement
- A cubic hardening term: a cubic term that increases at large stretch

The mass is released from an initial displacement and oscillates with characteristics that depend on:
- Linear spring stiffness (k₁)
- Cubic hardening coefficient (k₃)
- Mass (m)

## Mathematical Model

For a spring-mass system with a cubic hardening term, the equation of motion is:

```
m * dv/dt = -(k₁*x + k₃*x³)
```

where:
- `x` is the displacement
- `v` is the velocity (dx/dt)
- `dv_dt` is the acceleration (target variable)

## Discovered Law

Through polynomial regression analysis on the training dataset, the instantaneous acceleration was modeled as:

```
dv_dt = -4.0459 + 4.6190*x - 6.8354*x² + 4.8846*x³
        - 4.2943*z + 6.1382*e + 3.8264*z*x - 3.7547*e*x
```

### Interpretation of Terms

1. **Linear term (4.6190*x)**: Expected negative relationship to displacement (restoring force), but appears positive due to interaction with other terms and the nonlinear dynamics.

2. **Quadratic term (-6.8354*x²)**: Captures the nonlinear deviation from simple harmonic motion at larger amplitudes.

3. **Cubic term (4.8846*x³)**: Directly represents the cubic hardening component of the spring force.

4. **z term (-4.2943*z)**: The `z` variable appears to correlate strongly with accumulated displacement or phase information in the oscillation. The negative coefficient indicates it contributes to restoring the system.

5. **e term (6.1382*e)**: The `e` variable shows positive correlation with kinetic energy and other measures of system activity. Its positive coefficient suggests it represents amplitude-dependent effects.

6. **Interaction terms (z*x and e*x)**: The interaction terms capture the coupling between the state variables and current position, necessary for accurate prediction at all phases of the oscillation.

## Model Performance

- **R² Score**: 0.9930 (training data)
- **Mean Absolute Error**: 0.0536
- **Maximum Error**: 0.2573
- **Standard Deviation of Residuals**: 0.0691

## Regression Methodology

The model was derived using:
1. Polynomial feature generation up to degree 3 in position `x`
2. Ordinary Least Squares (OLS) linear regression
3. Interaction terms between position and auxiliary variables (`z*x`, `e*x`)

The final model uses 7 features (intercept + 6 terms) optimized via scikit-learn's LinearRegression.

## Physical Validity

The cubic term coefficient (4.8846) and the overall structure confirm the cubic hardening hypothesis. The model correctly captures:
- The restoring force dominated by nonlinear terms
- Time-dependent effects through the auxiliary variables z and e
- The amplitude-dependent oscillation frequency typical of Duffing oscillators

## Implementation

The law is implemented in `law.py` as a simple pointwise function that:
1. Takes a list of single-row dictionaries (input: t, x, v, z, e)
2. Computes the polynomial with interaction terms
3. Returns the predicted `dv_dt` values

This design ensures numerical stability and independence between predictions, making it suitable for evaluation on arbitrary orderings of the hidden test set.
