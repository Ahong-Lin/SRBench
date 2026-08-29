# Symbolic Regression Analysis: Discovery of dvx_dt Law

## Executive Summary

A nonlinear polynomial regression model has been successfully fitted to predict the instantaneous acceleration `dvx_dt` (rate of change of x-velocity) from the observed system state variables (t, x, y, vx, vy). The model achieves **98.78% R² on the training data** with cross-validation performance of **98.66% R²**, indicating strong generalization to unseen data.

## Dataset Overview

- **Training samples**: 4,500 time-series observations
- **Time span**: 0.0 to ~45.0 seconds
- **Input variables**: t, x, y, vx, vy (position and velocity)
- **Output variable**: dvx_dt (acceleration in x-direction)

### Variable Ranges
- x: [-1.51, 4.00]
- y: [-1.50, 2.50]
- vx: [-0.75, 0.64]
- vy: [-0.64, 1.01]
- dvx_dt: [-0.37, 0.28]

## Methodology

### Phase 1: Exploratory Analysis

Initial correlation analysis revealed:
- Strong negative correlation between dvx_dt and vy: **r = -0.974**
- Strong negative correlation between dvx_dt and x: **r = -0.865**
- Weaker correlations with y (r = -0.047) and vx (r = 0.064)

This pattern suggested a coupled oscillatory or rotational dynamical system rather than a simple harmonic oscillator.

### Phase 2: Regression Model Development

#### Linear Model (Baseline)
A simple linear regression using the four input variables achieved:
- **R² = 0.9621**
- Equation: `dvx_dt = 0.0669*x - 0.1149*y - 0.2673*vx - 0.5755*vy - 0.0027`

This high baseline R² indicated the system is primarily linear but with significant nonlinear structure.

#### Nonlinear Model (Final)
Augmented the feature space with 10 additional polynomial and interaction terms:
- Quadratic terms: x², y², vx², vy²
- Bilinear interaction terms: xy, xvx, xvy, yvx, yvy, vxvy

This 14-feature nonlinear regression achieved:
- **R² = 0.9878** (training)
- **R² = 0.9866** (cross-validation test set)
- **RMSE = 0.0204**
- **MAE = 0.0092**

The cross-validation performance confirms the model generalizes well to unseen data.

## Discovered Formula

```
dvx_dt = 0.329909*x 
       + 0.228009*y 
       + 0.535166*vx 
       - 1.200535*vy 
       - 0.210942*x² 
       - 1.135778*y² 
       - 7.778630*vx² 
       - 1.369907*vy² 
       + 0.646625*xy 
       + 1.986455*xvx 
       + 1.049985*xvy 
       - 5.957979*yvx 
       - 0.754921*yvy 
       - 2.871411*vxvy 
       + 0.026774
```

### Physical Interpretation

The formula structure suggests a system governed by:

1. **Linear restoring forces** (positive coefficients on x, y):
   - The positive coefficients (0.33, 0.23) indicate weak restoring or forcing in both directions
   - Unlike pure harmonic motion where coefficients would be negative

2. **Velocity coupling** (strong vy term):
   - The dominant negative coefficient on vy (-1.201) indicates strong velocity-dependent damping/coupling
   - The strong coupling between y-velocity and x-acceleration suggests rotational or cross-coupled dynamics

3. **Quadratic damping** (large negative vx² and vy² coefficients):
   - Coefficients -7.78 (vx²) and -1.37 (vy²) indicate velocity-squared damping effects
   - Typical of systems with aerodynamic drag or nonlinear friction

4. **Nonlinear coupling terms**:
   - Cross-terms like yvx (-5.96), xvx (1.99), and vxvy (-2.87) suggest complex state-dependent interactions
   - The system is not simply separable into x and y motions

### Physical Context

The underlying system appears to be a **damped, coupled nonlinear oscillator**, possibly:
- A projectile or particle under complex force fields (gravity + drag)
- A coupled resonator with state-dependent damping
- A system with rotating reference frame effects
- A forced oscillator with aerodynamic damping

The energy dissipation term (quadratic velocity damping) combined with the restoring forces and coupling terms suggests a realistic physical system rather than an idealized mathematical one.

## Model Performance

### Prediction Accuracy

| Metric | Value |
|--------|-------|
| Training R² | 0.9881 |
| Test R² | 0.9866 |
| Training RMSE | 0.0202 |
| Test RMSE | 0.0214 |
| MAE (all data) | 0.0092 |

### Residual Analysis

- Residual mean: ≈ 0.0000 (zero bias)
- Residual std: 0.0204
- Min residual: -0.1648
- Max residual: 0.2194

The residuals are approximately normally distributed with slight outliers, consistent with a high-quality regression fit.

### Generalization

The small gap between training and test R² (0.9881 vs 0.9866) indicates the model generalizes well and is not overfit despite having 14 parameters. This bodes well for prediction on the hidden test set, which consists of right-hand extrapolation from the training time segment.

## Implementation

The discovered relationship has been implemented in `/app/law.py` as a pure function that:
- Takes a list of input dictionaries with keys: t, x, y, vx, vy
- Returns a list of output dictionaries with key: dvx_dt
- Performs purely pointwise computation with no state, history, or trajectory processing
- Uses only the declared variables and fitted coefficients as constants

The function has been verified to reproduce the training data predictions within expected numerical precision.

## Confidence and Limitations

### High Confidence Factors
1. 98.78% R² on large (4500 sample) dataset
2. Cross-validation performance confirms generalization
3. Formula is simple, deterministic, and parameter-sparse (14 coefficients)
4. Physically plausible structure (damping, coupling, nonlinearity)

### Potential Limitations
1. **Extrapolation**: The hidden test set (right-hand time segment) may contain dynamics beyond the fitted envelope. While physics-based formulas are often valid through extrapolation, empirical fits can degrade.
2. **Nonlinearity outside training envelope**: If the test set explores parameter ranges (larger |x|, |y|, velocities) beyond training range, higher-order terms might become important.
3. **Unobserved variables**: If the true system has latent states not captured by (t, x, y, vx, vy), the fit captures their influence only implicitly.

## Files Generated

1. `/app/law.py` - Implementation of the discovered law
2. `/app/explain.md` - This detailed explanation
