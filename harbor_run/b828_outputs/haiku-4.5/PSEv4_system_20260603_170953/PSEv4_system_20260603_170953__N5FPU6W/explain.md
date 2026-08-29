# Discovered Acceleration Law

## Summary

The instantaneous acceleration `dv_dt` is described by a **degree-3 polynomial model** in the variables `t` (time), `x` (position), and `v` (velocity).

**Model Performance:**
- R² = 0.981723 (on training data with 1500 samples)
- RMSE = 0.166641
- MAE = 0.116796

## Mathematical Formulation

The discovered law is:

```
dv_dt = 0.350191
        - 0.00186011*t + 0.229438*x + 0.419189*v
        - 0.00070942*t² + 0.0221310*t*x - 0.0194561*t*v
        - 0.174428*x² - 0.0301024*x*v - 0.191282*v²
        + 0.0000103186*t³ - 0.000392593*t²*x + 0.000334464*t²*v
        + 0.00630762*t*x² + 0.00078155*t*x*v + 0.00762848*t*v²
        - 0.968626*x³ - 0.143859*x²*v - 0.0380786*x*v² - 0.0659835*v³
```

## Physical Interpretation

The dominant term is the **cubic position term** (`-0.969*x³`), which suggests the system experiences a strong cubic potential. This is characteristic of certain nonlinear oscillatory systems.

The key features of the discovered relationship:

1. **Cubic restoring force**: The `-0.969*x³` term dominates, providing the primary restoring force for the system
2. **Velocity influence**: The linear velocity term (+0.419*v) and quadratic damping term (-0.191*v²) suggest both linear drag and velocity-dependent effects
3. **Position-velocity coupling**: Terms like `-0.144*x²*v` indicate interaction between position and velocity
4. **Time dependence**: The intercept (0.350) and small time-dependent terms suggest either an external driving force or slight time-varying effects
5. **Quadratic position correction**: The `-0.174*x²` term provides a secondary restoring force

## Model Structure

This is a **purely algebraic (non-implicit) pointwise function** of the current state variables `(t, x, v)`. Each evaluation is independent and requires no integration or historical state.

The polynomial approximation captures:
- Nonlinear restoring forces (through cubic and quadratic terms in `x`)
- Velocity-dependent effects (linear and quadratic damping, plus couplings with position)
- Weak time-dependent effects (small coefficients on `t` terms, mostly through the intercept)

## Model Accuracy

The model achieves high accuracy across most of the data range:
- Particularly good performance in the main oscillation region (|v| < 1.0)
- Some systematic deviations in regions of extreme velocity (|v| > 1.2), but these are relatively rare in the training data
- Residuals are approximately normally distributed with mean near zero

## Coefficients at a Glance

| Term | Coefficient | Magnitude |
|------|-------------|-----------|
| x³ | -0.9686 | Dominant |
| v | +0.4192 | Second largest |
| x | +0.2294 | Third |
| x²·v | -0.1439 | Moderate |
| v² | -0.1912 | Moderate |
| x² | -0.1744 | Moderate |
| Intercept | +0.3502 | Baseline offset |

The remaining terms are small corrections that refine the prediction.

## Formula for Implementation

```python
dv_dt(t, x, v) = 0.350191
    - 0.00186011*t + 0.229438*x + 0.419189*v
    - 0.00070942*t² + 0.0221310*t*x - 0.0194561*t*v
    - 0.174428*x² - 0.0301024*x*v - 0.191282*v²
    + 0.0000103186*t³ - 0.000392593*t²*x + 0.000334464*t²*v
    + 0.00630762*t*x² + 0.00078155*t*x*v + 0.00762848*t*v²
    - 0.968626*x³ - 0.143859*x²*v - 0.0380786*x*v² - 0.0659835*v³
```
