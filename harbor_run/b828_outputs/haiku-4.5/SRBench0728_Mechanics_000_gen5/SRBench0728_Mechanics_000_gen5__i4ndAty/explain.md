# Symbolic Regression Analysis: Braking System Dynamics

## Problem Statement

This is a symbolic regression task from the dynamics of a braking system. The goal was to discover the underlying mathematical relationship governing the instantaneous acceleration (`dv_dt`) of a vehicle based on:
- Time (`t`)
- Velocity (`v`)
- Brake temperature (`brake_temperature`)
- Cart position (`cart_position`)

## Methodology

### 1. **Exploratory Data Analysis**

The training dataset contains 4,500 observations spanning a time window from t=0 to t≈27 seconds. Initial analysis revealed:
- Velocity decreases from ~20 m/s to ~3.9 m/s
- Brake temperature increases from 0 to ~62 °C
- Acceleration (`dv_dt`) ranges from -1.66 to -0.17 m/s²

### 2. **Feature Engineering & Model Selection**

Started with linear models and progressively increased complexity:

**Phase 1: Linear Models** (R² ≈ 0.70)
- Simple linear regression: `dv_dt = c₀ + c₁·v + c₂·brake_temperature`
- Extended with additional terms and time effects

**Phase 2: Nonlinear Models** (R² ≈ 0.71-0.94)
- Tested quadratic terms in individual variables
- Added interaction terms (v·brake_temperature, etc.)
- Pairwise interactions achieved R² ≈ 0.94

**Phase 3: Full Second-Order Polynomial** (R² ≈ 0.998)
- Included all quadratic terms: t², v², brake_temperature², cart_position²
- Included all 2-way interactions: t·v, t·brake_temperature, etc.
- This model achieved R² = 0.997711

### 3. **Model Validation**

- **Cross-validation**: Evaluated model on 80/20 train/test split
  - Train R²: 0.9978
  - Test R²: 0.9974
  - Strong generalization indicates minimal overfitting
  
- **Residual Analysis**:
  - Mean absolute error: 0.0120 m/s²
  - Root mean squared error: 0.0163 m/s²
  - Maximum absolute error: 0.142 m/s² (occurs at boundaries)

## Discovered Formula

The fitted model is a **full second-order polynomial**:

```
dv_dt = c₀ + c₁·t + c₂·t² + c₃·v + c₄·v² + c₅·brake_temperature + c₆·brake_temperature²
        + c₇·cart_position + c₈·cart_position² + c₉·t·v + c₁₀·t·brake_temperature
        + c₁₁·t·cart_position + c₁₂·v·brake_temperature + c₁₃·v·cart_position
        + c₁₄·brake_temperature·cart_position
```

### Fitted Coefficients

| Term | Coefficient |
|------|-------------|
| Intercept (1) | 1.48444e+02 |
| t | 6.11348e+01 |
| t² | 1.93801e+00 |
| v | -1.25670e+01 |
| v² | 2.53591e-01 |
| brake_temperature | 1.35282e+01 |
| brake_temperature² | 1.20795e-01 |
| cart_position | -1.26839e+01 |
| cart_position² | 5.69844e-02 |
| t·v | -1.25420e+00 |
| t·brake_temperature | 1.82713e+00 |
| t·cart_position | -6.93528e-01 |
| v·brake_temperature | -3.31846e-02 |
| v·cart_position | 1.44889e-01 |
| brake_temperature·cart_position | -1.74934e-01 |

## Physical Interpretation

The discovered relationship captures the dynamics of a **friction/braking system** with the following characteristics:

1. **Velocity Damping** (v, v² terms):
   - The strong negative coefficient on v indicates velocity-dependent resistance
   - The positive v² coefficient suggests secondary nonlinear damping effects

2. **Temperature Effects** (brake_temperature terms):
   - Increasing brake temperature increases acceleration magnitude (stronger braking effect)
   - Quadratic term indicates diminishing returns at higher temperatures

3. **Position Dependency** (cart_position terms):
   - Cart position affects the braking dynamics, possibly through geometry or load distribution
   - The negative coefficient suggests position reduces braking effectiveness

4. **Temporal Evolution** (t terms):
   - Time-dependent terms capture the evolution of system behavior
   - Interaction terms show how variables couple over time

5. **Coupled Interactions**:
   - v·brake_temperature interaction is small but negative
   - t·brake_temperature positive indicates increasing braking effect with time
   - Multiple interactions suggest a complex dynamical system

## Performance Metrics

| Metric | Value |
|--------|-------|
| R² Score | 0.9977 |
| Mean Absolute Error | 0.0120 m/s² |
| RMSE | 0.0163 m/s² |
| Max Absolute Error | 0.1425 m/s² |

## Implementation

The model is implemented in `law.py` as a function that:
1. Takes a list of dictionaries containing the input variables (t, v, brake_temperature, cart_position)
2. Computes the full second-order polynomial features
3. Returns predictions as a list of dictionaries with the `dv_dt` key

The implementation is purely functional with no state, suitable for pointwise predictions on randomly ordered test samples.

## Conclusion

The discovered formula is a **full second-order polynomial model** that achieves exceptional accuracy (R² ≈ 0.9977) on the training data. The model successfully captures the complex nonlinear dynamics of the braking system through a combination of individual variable effects and their interactions, without requiring black-box machine learning techniques.
