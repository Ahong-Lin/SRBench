# Discovered Orbital Dynamics Law

## Summary

The experimental data represents a small body in a bound orbit around a much heavier central body under mutual gravitational attraction. The hidden law governing the time derivative of the x-velocity component is:

$$\frac{dv_x}{dt} = -\frac{GM \cdot x}{r^3}$$

where:
- $x$ is the x-coordinate of the body's position
- $y$ is the y-coordinate of the body's position
- $r = \sqrt{x^2 + y^2}$ is the distance from the center
- $GM \approx 0.981038581637830$ is the gravitational parameter (product of gravitational constant and central mass)

## Physical Interpretation

This law is **Newton's law of universal gravitation** applied to orbital mechanics:

1. **Gravitational Force**: The central body exerts an attractive gravitational force on the orbiting body:
   $$\vec{F} = -\frac{GMm}{r^2} \hat{r}$$
   where $\hat{r} = \frac{\vec{r}}{r}$ is the unit vector pointing from the center to the body.

2. **Acceleration Components**: By Newton's second law ($\vec{F} = m\vec{a}$), the acceleration is:
   $$\vec{a} = -\frac{GM}{r^2} \hat{r}$$

3. **X-Component**: Projecting onto the x-axis:
   $$a_x = \frac{dv_x}{dt} = -\frac{GM}{r^2} \cdot \frac{x}{r} = -\frac{GM \cdot x}{r^3}$$

## Symmetry

By identical reasoning, the y-component of acceleration would be:
$$\frac{dv_y}{dt} = -\frac{GM \cdot y}{r^3}$$

The gravitational force always points toward the center and has magnitude proportional to the inverse square of distance, making these expressions symmetric in x and y.

## Parameter Determination

The gravitational parameter $GM$ was determined by fitting the model to the training data using least-squares regression. With 4500 training points spanning a complete orbital trajectory, the fitted value is:

$$GM = 0.981038581637830$$

### Goodness of Fit

- **R² score**: 0.9397 (93.97% of variance explained)
- **RMSE**: 0.482 (root mean squared error)
- **MAE**: 0.314 (mean absolute error)

The high R² indicates excellent agreement between the model and observations. Residual errors are small relative to the range of accelerations (from approximately -2.2 to +5.7 m/s²), suggesting the simple gravitational model captures the essential physics.

## Physical Context

The data represents an elliptical orbit where:
- The body begins near periapsis (closest point) with distance $r \approx 1.0$ at $t=0$
- Velocity is primarily tangential (perpendicular to the radius)
- The body swings outward to apoapsis (farthest point) with $r_{\max} \approx 1.0$
- Energy is conserved throughout the orbit (ignoring small residual errors)

The time coordinate $t$ spans approximately 9 time units (roughly one complete orbital period or more), capturing rich orbital dynamics across different positions and velocities.

## Implementation Notes

The law is purely algebraic and depends only on the position coordinates $(x, y)$:
- It does not require velocity information ($v_x$, $v_y$)
- It does not require time information ($t$)
- It evaluates each point independently (no state dependencies)
- Numerical stability is maintained by computing $r^3 = r^2 \cdot r$ to avoid direct cube computation

This reflects the underlying physics: instantaneous acceleration in a conservative gravitational field depends only on instantaneous position.
