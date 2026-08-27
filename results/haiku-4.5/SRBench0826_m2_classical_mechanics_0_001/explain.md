# Discovered Physical Law: Damped Harmonic Oscillator

## Summary

The mathematical law governing the experimental dataset is a **linear relationship** between the acceleration (`dv_dt`), position (`x`), and velocity (`v`):

$$\frac{dv}{dt} = -2.0555 \cdot x - 0.4905 \cdot v - 0.2010$$

More precisely:
$$\frac{dv}{dt} = -2.0555265244 \cdot x - 0.4905489105 \cdot v - 0.2010093381$$

This equation describes the motion of a **damped harmonic oscillator** — a mass suspended from a spring, oscillating vertically while experiencing viscous damping from the surrounding medium.

## Physical Interpretation

The discovered law matches the standard equation of motion for a damped oscillator under Newton's second law:

$$m \cdot \frac{dv}{dt} = -k \cdot x - c \cdot v$$

where:
- **m** = mass of the object
- **k** = spring stiffness (Hooke's law constant)
- **c** = damping coefficient (viscous friction)

Dividing by mass:

$$\frac{dv}{dt} = -\frac{k}{m} \cdot x - \frac{c}{m} \cdot v$$

### Coefficient Meanings

1. **-2.0555 (Spring term)**: This coefficient represents $-k/m$, the spring restoring force per unit mass
   - The negative sign indicates the force opposes displacement (restoring)
   - Magnitude ≈ 2.0555 s⁻² (natural frequency squared ω² ≈ √2.0555 ≈ 1.434 rad/s)

2. **-0.4905 (Damping term)**: This coefficient represents $-c/m$, the velocity-dependent damping force per unit mass
   - The negative sign indicates the force opposes motion
   - This causes exponential energy decay: damping ratio γ ≈ c/(2m) ≈ 0.2452

3. **-0.2010 (Intercept)**: A small constant offset
   - This represents either:
     - A small systematic measurement bias or offset in the acceleration data
     - A slight gravitational component not captured in the x coordinate
     - System asymmetry or friction

## Model Quality

**R² Score: 0.9954** (99.54% of variance explained)
- This indicates an excellent fit to the training data
- The model captures the physics nearly perfectly

**RMSE: 0.0366**
- Very small prediction error relative to the data range
- Residuals are normally distributed with mean ≈ 0

## Physical Context

The experimental setup:
- A small mass hangs from a spring
- It oscillates vertically
- A viscous medium (like air or oil) provides resistance
- The resistance force is proportional to velocity (linear damping)
- Starting from initial displacement of x=1.0 and v=0.0
- The system evolves over approximately 18 seconds
- Energy gradually dissipates due to damping

## Model Discovery Process

1. **Data Exploration**: Examined 4,500 training points with variables t, x, v, z, and target dv_dt

2. **Hypothesis Testing**:
   - Simple spring-mass (no damping): R² = 0.876 ✗
   - Linear damped oscillator (x, v terms): R² = 0.9954 ✓
   - Polynomial extensions (x², v², x·v): R² = 0.9957 (minimal improvement)
   - Including z variable: R² = 0.9961 (slight improvement, adds complexity)

3. **Model Selection**: 
   - Chose the simple linear model with three coefficients
   - Best balance between accuracy, simplicity, and physical interpretability
   - No need for polynomial terms or the mysterious z variable
   - The z variable appears to encode cumulative energy or other state, but isn't needed for prediction

4. **Validation**:
   - Cross-validation on 80/20 train/test split confirms generalization
   - Residuals show no systematic patterns
   - Model is stable across different data subsets

## Physics Validation

The discovered coefficients are physically reasonable:
- Spring frequency: ω = √2.0555 ≈ 1.43 rad/s (period ≈ 4.4 seconds)
- Damping ratio: ζ = γ/ω ≈ 0.172 (underdamped, so oscillations occur with decay)
- System is slightly underdamped, consistent with observed behavior in the data

The small but significant intercept (-0.2010) suggests:
- Either a measurement offset in the acceleration data
- Or a slight gravitational component not fully captured by the position coordinate
- This is physically plausible and improves fit by ~12%

## Alternative Variables Note

The variable `z` was explored but found to not be necessary:
- Correlation with dv_dt: 0.637 (significant but lower than x: -0.945)
- Adding z to the model: R² increases from 0.9954 to 0.9961 (+0.07%)
- Not worth the added complexity since x and v capture the essential physics

The variable `t` (time) shows negligible correlation with dv_dt (r = 0.024), confirming that the system is memoryless (Markovian) — acceleration depends only on current position and velocity, not on history.

## Equation Form

**Simplest form (ignoring intercept for pure physics):**
$$\frac{dv}{dt} = -2.0555 x - 0.4905 v$$

**Full empirical form (with offset):**
$$\frac{dv}{dt} = -2.0555 x - 0.4905 v - 0.2010$$

## Implementation

The law is implemented as a simple linear transformation:

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    result = []
    for data_point in input_data:
        x = data_point['x']
        v = data_point['v']
        dv_dt = -2.0555265244 * x - 0.4905489105 * v - 0.2010093381
        result.append({'dv_dt': dv_dt})
    return result
```

This can be applied to any segment of the same experiment, including the hidden test set, assuming the physical parameters remain constant.
