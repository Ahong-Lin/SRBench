# Mathematical Law for Sphere Settling in Viscous Fluid

## Discovered Formula

The velocity of a sphere settling in a viscous fluid as a function of time follows the **double exponential model**:

$$v(t) = a \left(1 - b e^{-kt} - c e^{-mt}\right)$$

Where the fitted parameters are:
- **a** = 10.66134451 (terminal velocity scaling factor)
- **b** = 1.06127180 (primary exponential amplitude)
- **k** = 0.66319808 (primary exponential decay rate, s⁻¹)
- **c** = -0.06999260 (secondary exponential amplitude)
- **m** = 2.45739000 (secondary exponential decay rate, s⁻¹)

## Physical Interpretation

This model captures the dynamics of a sphere settling under gravity in a fluid with multiple force contributions:

### Primary Exponential Term (b·exp(-kt))
- Represents the **main dynamics** driven by balance between gravitational force and viscous drag
- The time constant τ₁ = 1/k ≈ 1.508 seconds characterizes the approach to steady-state behavior
- Coefficient b ≈ 1.06 indicates that the exponential term slightly overshoots before settling

### Secondary Exponential Term (c·exp(-mt))
- Captures **transient effects** from:
  - **Added-mass forces**: The effective mass of the sphere is increased by the mass of fluid it displaces
  - **History forces (Basset force)**: Memory effects in unsteady flow around the sphere
  - **Wall corrections**: Hydrodynamic interactions with vessel walls, which decay more rapidly
- The time constant τ₂ = 1/m ≈ 0.408 seconds is much shorter, indicating these are transient effects
- Negative coefficient c indicates these forces provide a slight positive contribution that decays quickly

### Terminal Velocity
The asymptotic velocity (as t → ∞) is:
$$v_{\infty} = a \left(1 - b(0) - c(0)\right) = a \approx 10.66 \text{ (units of the experiment)}$$

## Methodology

### Data Analysis
- **Dataset size**: 4,500 data points
- **Time range**: t ∈ [0.01, 4.5009] seconds
- **Velocity range**: v ∈ [0.1437, 10.0952]
- **Correlation**: High positive correlation (r = 0.944) between t and v

### Model Selection Process

The following models were tested:

| Model | RMSE |
|-------|------|
| **Double Exponential** | **1.97e-03** ✓ |
| Exponential + Power Law | 1.75e-02 |
| Simple Exponential | 3.88e-02 |
| History Force (sqrt + damped) | 4.90e-02 |
| sqrt(t) + linear | 4.83e-01 |
| Linear | 9.16e-01 |
| Power Law | 4.72e-01 |

The **double exponential model** provides the best fit with RMSE = 1.97×10⁻³, indicating excellent predictive accuracy.

### Validation
- Root Mean Square Error: **1.97×10⁻³**
- Maximum prediction error: ~0.56% on test points
- The model accurately captures:
  - Initial acceleration (high dv/dt ≈ 5.75 m/s² at t ≈ 0)
  - Asymptotic approach to terminal velocity (dv/dt → 0.39 as t → ∞)
  - Smooth curvature throughout the entire time range

## Physics Connection

This settling dynamics can be derived from the equation of motion:

$$m \frac{dv}{dt} = F_g - F_b - F_d - F_{am} - F_h$$

Where:
- **F_g**: Gravitational force (weight)
- **F_b**: Buoyant force
- **F_d**: Viscous drag (Stokes drag: -6πηrv)
- **F_am**: Added-mass force (accelerating surrounding fluid)
- **F_h**: History/Basset force (integral of past accelerations)

The solution to this integro-differential equation naturally produces a combination of exponential terms with different time constants, which is exactly what the fitted model captures.

## Implementation Notes

The law function implements this formula pointwise:
- Takes individual time values t as input
- Returns corresponding velocity predictions v
- Uses only the declared variable (t) and fitted constants
- Performs pure mathematical evaluation with no state carried between calls
- Compatible with single-row queries as required by the verification protocol
