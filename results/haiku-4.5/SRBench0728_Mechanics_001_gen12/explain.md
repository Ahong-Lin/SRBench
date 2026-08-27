# Symbolic Regression Analysis: Discovered Law

## Executive Summary

The underlying mathematical relationship governing the observed dynamical system is surprisingly simple:

$$\frac{dx}{dt} = v$$

**The rate of change of position (dx_dt) is exactly equal to the velocity (v).**

This is a fundamental kinematic relationship from physics: the time derivative of position is velocity.

---

## Discovered Formula

```
dx_dt = v
```

### Formula Interpretation

- **dx_dt**: The instantaneous rate of change of position (what we predict)
- **v**: The instantaneous velocity of the system
- **Coefficients**: Implicit coefficient = 1.0

### Fitted Parameters

There are no fitted parameters in this law—the relationship is exact and deterministic with unit coefficient.

---

## Methodology

### 1. Data Exploration

The training dataset contains 4,500 observations with the following features:
- `t` (time): continuous variable from 0 to ~18 seconds
- `x` (position): observed state variable ranging from ~-1.14 to ~1.17
- `v` (velocity): observed state variable ranging from ~-1.21 to ~1.21
- `Fh` (force harmonic): applied force signal, correlation with dx_dt: -0.61
- `Fh2` (force harmonic 2): second force component, correlation with dx_dt: -0.95
- `dx_dt` (target): rate of change of position, to be predicted

### 2. Correlation Analysis

Initial analysis revealed:

| Feature | Correlation with dx_dt |
|---------|------------------------|
| v       | **1.000000** (perfect) |
| Fh      | -0.607622             |
| Fh2     | -0.953150             |
| t       | 0.261171              |
| x       | 0.017009              |

The perfect correlation between `v` and `dx_dt` immediately suggested they are identical.

### 3. Verification

Direct comparison confirmed:
- **Max difference** between v and dx_dt: 0.0 (within machine precision)
- **Mean difference**: 0.0
- **Standard deviation of differences**: ~10⁻¹⁶ (floating-point rounding noise)
- **Exact equality test**: v == dx_dt for all 4,500 rows ✓

### 4. Regression Validation

Multiple regression approaches all converged to the same conclusion:

| Approach | R² Score | Findings |
|----------|----------|----------|
| Linear regression (v, Fh, Fh2) | 1.0 | Coefficients: v=1.0, Fh≈0, Fh2≈0 |
| All features (t, x, v, Fh, Fh2) | 1.0 | Only v term is significant |
| Polynomial degree-2 | 1.0 | Confirms no non-linear interaction needed |

### 5. Physical Interpretation

This result makes physical sense:
- **v is the velocity**: By definition in kinematics, velocity is the first time derivative of position
- **dx_dt is the rate of change of position**: This is exactly the definition of velocity
- **Forces don't affect the kinematic relationship**: While Fh and Fh2 represent applied forces that would affect the acceleration (and thus eventually velocity and position through integration), they do not alter the instantaneous kinematic relationship
- **This is not a force equation (F=ma)**: The system appears to report pre-computed velocity values, not accelerations

---

## Model Performance

**Perfect prediction on training data:**
- Mean Squared Error (MSE): 0.0
- Root Mean Squared Error (RMSE): 0.0
- Mean Absolute Error (MAE): 0.0
- Maximum Absolute Error: 0.0
- Correlation with actual values: 1.0

**Expected generalization:**
Since this is a fundamental kinematic identity (not a fitted empirical model), the law should extrapolate perfectly to the right-hand time segment and any other experimental conditions where the system maintains the same kinematic principles.

---

## Robustness Analysis

### Across Different Time Periods

The relationship holds consistently across the entire observed time window (0 to ~18 seconds):
- Early time (t ≈ 0): ✓ Exact equality
- Mid time (t ≈ 9): ✓ Exact equality
- Late time (t ≈ 18): ✓ Exact equality

### Independence from Applied Forces

Although Fh and Fh2 show strong correlations with dx_dt (likely because they influence the overall system dynamics), they are not needed to predict dx_dt when v is available. This suggests:
- The system state is Markovian: knowing v is sufficient to determine dx_dt
- Forces operate through other state variables (likely affecting acceleration/velocity evolution)

---

## Conclusion

The discovered symbolic regression law is the fundamental kinematic identity:

$$\boxed{\frac{dx}{dt} = v}$$

This is not an empirically fitted model but a physical law. The velocity observed in the data IS the rate of change of position by definition. The test set (right-hand extrapolation) should be predicted with perfect accuracy by simply returning the velocity values.
