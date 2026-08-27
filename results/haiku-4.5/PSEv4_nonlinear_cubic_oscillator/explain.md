# Mathematical Relationship Discovery

## Discovered Formula

The hidden mathematical relationship governing the dataset is a **polynomial regression model** with the following structure:

```
dv_dt = c₀ + c₁·x + c₂·x² + c₃·v + c₄·v² + c₅·x·v + c₆·v³ + c₇·x·v² + c₈·t + c₉·v·t
```

## Model Parameters

| Parameter | Coefficient | Feature |
|-----------|-------------|---------|
| c₀ | +0.355241 | Intercept (constant) |
| c₁ | -1.797918 | x (linear) |
| c₂ | -1.626341 | x² (quadratic) |
| c₃ | -1.026893 | v (linear) |
| c₄ | -3.479356 | v² (quadratic) |
| c₅ | -1.783570 | x·v (interaction) |
| c₆ | -2.626073 | v³ (cubic) |
| c₇ | -0.883469 | x·v² (interaction) |
| c₈ | -0.007797 | t (linear, small effect) |
| c₉ | -0.178038 | v·t (interaction) |

## Model Performance

- **R² Score**: 0.9877 (explains 98.77% of variance)
- **Training RMSE**: 0.0398
- **Cross-Validation MSE**: 0.001599 ± 0.000027
- **Training Data Points**: 4,500

## Discovery Process

1. **Initial Analysis**: Examined correlations with individual variables
   - Strong correlation with x: -0.696
   - Weak correlation with v and t individually

2. **Feature Engineering**: Added polynomial and interaction terms
   - x² improved fit significantly
   - v² and v³ terms crucial for capturing nonlinear behavior
   - x·v and x·v² interactions important

3. **Iterative Refinement**: 
   - Initial model (x, x², x·v): R² = 0.708
   - Added v terms: R² = 0.961
   - Added t interactions: R² = 0.988

4. **Validation**: 5-fold cross-validation confirms stable generalization

## Interpretation

The model captures a complex, nonlinear relationship where:
- **x is the primary driver**, with both linear and quadratic contributions pulling dv_dt downward
- **v has strong nonlinear effects** including quadratic and cubic terms, also generally decreasing dv_dt
- **Interactions between x and v** are significant, showing they don't act independently
- **Time t has a minor direct effect** but interacts with v through the v·t term
- The predominance of negative coefficients suggests the system exhibits damping or dissipative behavior

This polynomial form suggests the underlying system may be governed by differential equations with damping and nonlinear terms, characteristic of many physical systems (e.g., damped oscillators with position-dependent damping).
