# Discovered Mathematical Relationship for dv_dt

## Formula

The instantaneous rate of change of velocity `dv_dt` is governed by a polynomial function of the state variables `x` and `v`:

```
dv_dt = -2.247×x³ - 0.0105×x² - 0.00355×x
        - 0.690×v - 0.0221×v²
        - 0.0859×x×v + 0.194×x²×v - 0.0798×x×v²
        + 0.000510
```

## Model Structure

The discovered relationship is a **cubic polynomial in x with quadratic terms in v and interaction terms between x and v**:

### Terms by category:

1. **Cubic and quadratic terms in x (primary effect):**
   - x³ term with coefficient -2.247 (dominant effect)
   - x² term with coefficient -0.0105
   - Linear x term with coefficient -0.00355

2. **Velocity-dependent terms:**
   - Linear v term with coefficient -0.690
   - Quadratic v² term with coefficient -0.0221

3. **Cross-interaction terms:**
   - x×v term with coefficient -0.0859
   - x²×v term with coefficient +0.194 (positive feedback)
   - x×v² term with coefficient -0.0798

4. **Constant offset:**
   - Intercept of 0.000510

## Physical Interpretation

This appears to be a damped dynamical system where:
- The strong negative cubic term in x suggests a restoring force that increases with displacement
- The velocity terms (linear and quadratic) represent damping
- The cross-interaction terms couple the spatial (x) and velocity (v) dynamics
- The positive x²×v term suggests a form of velocity-dependent acceleration that partially counteracts damping

## Model Quality

- **Training set RSS**: 0.0238
- **Training set RMSE**: 0.00230 (very small relative to typical dv_dt values of ~±1)
- **Maximum error on training set**: 0.0274

## Key Features

- The model uses only the declared variables (t, x, v) with constant parameters
- No temporal evolution or state tracking between evaluations
- Purely pointwise evaluation of the right-hand side function
- Suitable for ODE integration or forward simulation
