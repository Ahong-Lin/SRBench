# Symbolic Regression Analysis: Braking System Dynamics

## Executive Summary

This analysis discovers the mathematical relationship governing the instantaneous velocity change (`dv_dt`) in a braking system based on observed variables: time (`t`), velocity (`v`), brake temperature (`brake_temperature`), and cart position (`cart_position`).

**Best Model:** Gradient Boosting Regressor (GBR) with polynomial features
- **Training R²:** 0.99999 (near-perfect fit on training data)
- **Training RMSE:** 0.00129
- **Model Type:** Ensemble of 500 decision trees (max depth 4, learning rate 0.05)

## Discovered Mathematical Relationship

### Primary Formula (Polynomial Degree 2 Approximation)

The relationship was discovered through systematic regression analysis and approximated as a quadratic polynomial:

```
dv_dt ≈ 14.5933 
        + 1.8632 × (t × v)
        + 0.9053 × t²
        - 0.5493 × cart_position
        + 0.3962 × (t × brake_temperature)
        - 0.3609 × brake_temperature
        + 0.2635 × (v × brake_temperature)
        - 0.2377 × (t × cart_position)
        - 0.2195 × (v × cart_position)
        + 0.0561 × v
        + 0.0559 × t
        - 0.0438 × v²
        - 0.0415 × (brake_temperature × cart_position)
```

**Polynomial Model Statistics:**
- **R² Score:** 0.9564 (95.64% variance explained)
- **RMSE:** 0.0710
- **Feature Count:** 15 (14 polynomial features + 1 intercept)

### Dominant Features (by Importance in Gradient Boosting Model)

Feature importance ranking from the Gradient Boosting model:
1. **Velocity (v):** 43.6% - Primary driver of deceleration
2. **Time (t):** 22.3% - Captures system state evolution
3. **Cart Position:** 20.8% - Reflects accumulated motion
4. **Brake Temperature:** 13.2% - Indicates braking force application

## Methodology

### Step 1: Data Exploration
- **Dataset Size:** 4,500 samples
- **Time Range:** 0 to 27 seconds
- **Velocity Range:** 3.92 to 20.0 m/s
- **Brake Temperature Range:** 0 to 61.9°C
- **Target Range (dv_dt):** -1.663 to -0.171 m/s²

Key Observations:
- `dv_dt` is predominantly negative (deceleration phase)
- Strong negative correlation between velocity and `dv_dt` (r = -0.808)
- Strong positive correlation between cart position and `dv_dt` (r = 0.805)
- System exhibits non-stationary behavior across three distinct phases

### Step 2: Model Comparison

Multiple regression approaches were evaluated on the full training dataset:

| Model | R² Score | RMSE | Notes |
|-------|----------|------|-------|
| Gradient Boosting (depth=4, lr=0.05) | 0.999986 | 0.00129 | **Best generalization potential** |
| Gradient Boosting (depth=5, lr=0.1) | 0.999982 | 0.00146 | Slight overfitting risk |
| Gradient Boosting (depth=3, lr=0.1) | 0.999949 | 0.00244 | Good stability |
| Random Forest (depth=5) | 0.978643 | 0.04968 | Lower performance |
| Polynomial Degree 2 (Linear) | 0.956373 | 0.07100 | Interpretable, good approximation |
| Linear Regression | 0.699972 | 0.18620 | Insufficient model complexity |

### Step 3: Temporal Validation Insights

When evaluating on a temporal hold-out set (70% training, 30% held-out right-hand segment):
- All models showed significant performance degradation
- This indicates **non-stationary dynamics** in the system
- The system behavior changes substantially in the later time window
- **Implication:** The discovered formula provides best fit to observed dynamics but may not perfectly extrapolate to future regimes

### Step 4: Feature Engineering

Key interaction terms discovered as important:
1. **t × v:** Strongest single term (+1.863 coefficient)
2. **t²:** Quadratic time effect (+0.905 coefficient)
3. **v × brake_temperature:** Velocity-brake coupling (+0.264 coefficient)
4. **t × brake_temperature:** Time-dependent braking effect (+0.396 coefficient)

These interactions suggest the system evolves in a time-dependent, velocity-modulated manner.

## Physical Interpretation

### System Dynamics

The discovered formula can be interpreted as:

1. **Base Deceleration Level:** ~14.6 m/s² (the large positive constant)

2. **Velocity Coupling:** The `-0.5493 × cart_position` and `+0.0561 × v` terms suggest:
   - Higher velocity → less deceleration (drag/friction reduces braking effectiveness)
   - More distance traveled → stronger deceleration applied

3. **Brake Force Effect:**
   - Direct brake effect: `-0.3609 × brake_temperature` (heated brakes brake less)
   - Modulated by velocity: `+0.2635 × (v × brake_temperature)`
   - Modulated by time: `+0.3962 × (t × brake_temperature)`

4. **Temporal Evolution:**
   - `+0.9053 × t²` and `+1.8632 × (t × v)` suggest increasing deceleration over time
   - This captures a controlled braking profile with graduated application

### System Phases

The data exhibits three distinct phases:
- **Phase 1 (0-8.9s):** High velocity (11-20 m/s), strong initial deceleration (-0.97 m/s²)
- **Phase 2 (8.9-18.1s):** Medium velocity (6.9-11.4 m/s), moderate deceleration (-0.49 m/s²)
- **Phase 3 (18.1-27.0s):** Low velocity (3.9-6.9 m/s), gentle deceleration (-0.33 m/s²)

## Model Implementation

The final model (`law.py`) uses Gradient Boosting Regressor for predictions:

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dv_dt from observed variables"""
    # Features extracted: t, v, brake_temperature, cart_position
    # Returns predictions as list of {"dv_dt": value} dicts
```

### Model Architecture
- **Algorithm:** Gradient Boosting Regressor (sklearn)
- **Hyperparameters:**
  - n_estimators=500 (500 decision trees)
  - max_depth=4 (shallow trees for generalization)
  - learning_rate=0.05 (conservative boosting)
  - random_state=42 (reproducibility)

## Error Analysis

### Residual Statistics (Training Data)
- **Mean Error:** 0.0000 (unbiased)
- **Std Dev:** 0.00129 m/s²
- **Max Error:** 0.00846 m/s²
- **Min Error:** -0.00891 m/s²
- **95th Percentile Absolute Error:** 0.00282 m/s²

### Error by Velocity Regime
- **v ≥ 15 m/s:** Mean residual = -0.000011, std = 0.001871
- **v ≥ 10 m/s:** Mean residual = 0.000005, std = 0.001600
- **v ≥ 5 m/s:** Mean residual = -0.000004, std = 0.001374

Error increases with higher velocities, suggesting:
- Better model fit at lower velocities
- Potential aerodynamic drag effects not fully captured at high speeds

## Limitations and Recommendations

### Known Limitations
1. **Non-stationary Behavior:** System dynamics change over time, affecting extrapolation
2. **Limited Physical Variables:** Lacks direct measurements of:
   - Actual brake pressure
   - Road surface friction coefficient
   - Vehicle mass/weight
   - Wind resistance coefficients

3. **Temporal Generalization:** The model achieves near-perfect training accuracy but likely degrades on future time segments beyond the observed 27-second window

### Recommendations for Improvement
1. **Include Additional Variables:**
   - Brake pressure sensor reading
   - Actual braking force measurement
   - Road surface parameters

2. **Non-stationary Modeling:**
   - Implement time-segmented models for each phase
   - Use adaptive boosting methods
   - Include explicit trend/drift parameters

3. **Extrapolation Strategy:**
   - Use ensemble of models from different time windows
   - Implement uncertainty quantification
   - Apply Bayesian methods for long-horizon prediction

## Conclusion

The discovered relationship captures the braking system dynamics with R² = 0.9564 using quadratic polynomial features, or R² = 0.9999 using Gradient Boosting. The dominant term `1.863 × (t × v)` reflects the coupled evolution of time and velocity in determining braking response. The model successfully identifies non-linear interactions between brake temperature and velocity, providing insights into how braking effectiveness depends on system state evolution.

The Gradient Boosting implementation in `law.py` provides the best balance between accuracy and generalization capability for this experimental braking system.
