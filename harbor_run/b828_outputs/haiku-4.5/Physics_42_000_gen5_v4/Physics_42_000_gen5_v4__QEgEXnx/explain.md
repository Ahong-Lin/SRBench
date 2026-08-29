# Discovered Mathematical Law for Settling Velocity in Viscous Fluid

## Mathematical Formula

The velocity `v` as a function of time `t` is described by a **hyperbolic tangent (tanh) model**:

```
v(t) = a + b·tanh(c·(t + d))
```

Where:
- `a = -15.8585782809` (vertical offset)
- `b = 26.4331425965` (amplitude)
- `c = 0.3625923258` (rate parameter/steepness)
- `d = 1.9185199092` (horizontal shift)

### Explicit Form

```
v(t) = -15.8585782809 + 26.4331425965·tanh(0.3625923258·(t + 1.9185199092))
```

## Physical Interpretation

The hyperbolic tangent model is physically meaningful for settling velocity in a viscous fluid:

1. **Initial Phase (t → 0)**: The velocity starts at a finite value (approximately 0.104 at t=0.01)
2. **Transition Phase (0.01 < t < 2)**: Velocity increases rapidly as drag, added-mass, and history forces interact
3. **Asymptotic Phase (t → ∞)**: The tanh function asymptotically approaches a terminal velocity of approximately:
   ```
   v_terminal = a + b = -15.8585782809 + 26.4331425965 ≈ 10.575
   ```

The tanh function naturally captures:
- The smooth transition from initial acceleration to terminal velocity
- The decreasing rate of velocity change (dv/dt decreases over time)
- The mathematical signature of drag-dominated motion with memory/history effects

## Methodology

### Model Selection Process

Multiple candidate models were tested against the 4500 data points:

1. **Logarithmic Model**: `v = a + b·log(t + c)`
   - R² = 0.9936, RMSE = 0.2214
   - Good but not optimal

2. **Power Law Model**: `v = a·(t + c)^b`
   - Failed to converge with standard parameters

3. **Error Function Model**: `v = a + b·erf(c·(t + d))`
   - R² = 0.9999740, RMSE = 0.0141
   - Very good fit

4. **Hyperbolic Tangent Model**: `v = a + b·tanh(c·(t + d))` ✓ **SELECTED**
   - R² = 0.9999888, RMSE = 0.0093
   - **Best fit with lowest error**

5. **Square Root Model**: `v = a + b·√(t + c)`
   - R² = 0.9226, RMSE = 0.7698
   - Poor fit

### Fitted Parameters

The parameters were determined using non-linear least squares optimization with curve fitting:

| Parameter | Value | Meaning |
|-----------|-------|---------|
| a | -15.8585782809 | Vertical offset ensuring correct limiting behavior |
| b | 26.4331425965 | Amplitude of the tanh transition |
| c | 0.3625923258 | Rate of change (controls steepness of transition) |
| d | 1.9185199092 | Horizontal shift in the time domain |

## Fit Quality

### Error Metrics

- **R² (Coefficient of Determination)**: 0.9999888113
  - Indicates 99.99888% of variance explained
  - Nearly perfect fit
  
- **RMSE (Root Mean Square Error)**: 0.0092536157
  - Typical prediction error across all 4500 points
  - Represents approximately 0.09% relative error at v ≈ 10
  
- **Maximum Absolute Error**: 0.0392657179
  - Occurs at the boundary (very early times, t ≈ 0.01)
  - Still less than 0.4% of the maximum velocity value
  
- **Mean Absolute Error**: 0.0078463069
  - Average deviation between model and data

### Error Distribution

The largest errors occur at the boundaries:
- At t = 0.01 (very start): error ≈ 0.0393
- At t = 4.5 (end): error ≈ 0.0187
- In the middle range (1 < t < 4): error < 0.01

This pattern suggests the model is near-optimal, with any errors likely due to:
- Initial transient effects in the experimental setup
- Numerical precision limits of the fitting algorithm
- Possible experimental measurement noise

## Reasoning

### Why Hyperbolic Tangent?

The data exhibits classic characteristics of a sigmoid curve:

1. **Monotonic Increase**: v increases monotonically with t
2. **Decreasing Derivative**: dv/dt starts high (~5.75) and decreases to low values (~0.39)
3. **Asymptotic Behavior**: Approaches a limiting velocity as t → ∞
4. **Smooth Transitions**: No discontinuities or sharp transitions

The hyperbolic tangent function provides:
- A natural smooth transition mechanism
- Bounded behavior (range: -1 to +1)
- Mathematical elegance for physical phenomena
- Better fit than alternatives (R² = 0.9999888 vs 0.9999740 for erf)

### Physical Context

For a sphere settling in viscous fluid with drag, added-mass, history-force, and wall-correction terms:
- The equation of motion is nonlinear and involves memory effects
- These effects cause the velocity to evolve smoothly toward a terminal value
- The tanh model captures this behavior remarkably well

### Validation

The model was validated by:
1. Testing on random samples across the entire t range
2. Checking asymptotic behavior matches physics expectations
3. Verifying monotonicity and smoothness properties
4. Confirming low error metrics across the training set

## Conclusion

The discovered law is:

```
v(t) = -15.8585782809 + 26.4331425965 · tanh(0.3625923258 · (t + 1.9185199092))
```

This hyperbolic tangent model provides an accurate, interpretable, and physically meaningful representation of the settling velocity dynamics in the experimental data, achieving an R² of 0.9999888 with RMSE of 0.00925.
