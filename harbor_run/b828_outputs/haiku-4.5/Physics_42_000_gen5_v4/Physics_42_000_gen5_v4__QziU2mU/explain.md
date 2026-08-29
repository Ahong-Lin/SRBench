# Symbolic Regression Analysis: Sphere Settling in Viscous Fluid

## Discovered Mathematical Formula

The velocity `v` of a sphere settling in a viscous fluid as a function of time `t` is described by:

$$v(t) = at^3 + bt^2 + ct + d$$

where:
- **a** = 0.1075364099
- **b** = -1.3244644224
- **c** = 6.0209230962
- **d** = 0.0724816970

## Methodology

### 1. Initial Exploration
The training dataset contains 4500 observations of settling velocity `v` across a time range from t = 0.01 to t ≈ 4.50. Initial analysis revealed that velocity increases with time, with ratios between consecutive values hovering around 1.03, suggesting non-linear growth.

### 2. Model Comparison
I systematically tested several candidate models:

| Model | Form | MSE | R² |
|-------|------|-----|-----|
| Linear | v = at + b | 0.8398 | - |
| Quadratic | v = at² + bt + c | 0.0342 | - |
| **Cubic** | v = at³ + bt² + ct + d | **0.000224** | **0.999971** |
| Square Root | v = a√t + b | 0.1868 | - |
| Power Law | v = at^p + b | 0.1106 | - |
| Exponential | v = v_∞(1 - e^(-kt)) | 0.0015 | - |

### 3. Cubic Model Selection
The cubic polynomial provided the best fit with:
- **Mean Squared Error (MSE)**: 0.0002244477
- **Root Mean Squared Error (RMSE)**: 0.0149816
- **R² Score**: 0.9999707

This indicates the model explains 99.997% of the variance in the data.

### 4. Residual Analysis
The residuals from the cubic fit show excellent properties:
- **Mean residual**: ~0 (1.35 × 10⁻¹⁵, essentially machine precision)
- **Standard deviation**: 0.0150
- **Range**: -0.0509 to +0.0223

The small, symmetric residuals centered near zero indicate the model captures the underlying physics well.

## Physical Interpretation

In fluid dynamics, the settling of a sphere in a viscous medium with drag, added-mass effects, history forces, and wall corrections typically results in non-linear velocity evolution. The cubic polynomial represents a compact empirical model that captures:

1. **Initial phase**: Linear acceleration dominated by viscous drag and buoyancy
2. **Intermediate phase**: Transition as added-mass and history forces become significant
3. **Terminal phase**: Approach to terminal velocity with subtle higher-order effects

The negative coefficient on the t² term (b = -1.324) creates a slight deceleration in the middle range before the cubic term (a = 0.108 > 0) dominates again at larger times, reflecting the complex interaction of multiple force terms mentioned in the problem context.

## Implementation

The discovered law is implemented in `law.py` as a pointwise function that evaluates the cubic polynomial for each input time value independently, requiring only the input time `t` and the fitted coefficients.
