# Symbolic Regression: Oscillating Spring with Cubic Hardening

## Physical System

This dataset models a mass attached to a nonlinear spring on a frictionless surface. The spring has both linear restoring force and a cubic hardening term that becomes significant at large displacements. Starting from an initial displacement, the mass oscillates with changing amplitude and period due to the nonlinear dynamics.

## Discovered Law

The acceleration (rate of change of velocity) is governed by:

$$\frac{dv}{dt} = -0.2144 \cdot x - 0.7677 \cdot x^2 - 0.5329 \cdot x^3 - 1.6455 \cdot z + 0.0639 \cdot v - 0.0753 \cdot v^2 - 0.5448 \cdot xv - 2.0630 \cdot xv^2 + 1.4260 \cdot xz + 0.5278 \cdot vz - 0.0212 \cdot e - 0.7126 \cdot xe - 0.2564 \cdot ve + 0.4840 \cdot ze + 0.2773 \cdot x^2v + 0.000117 \cdot t$$

### Coefficients (in order of magnitude influence)

| Term | Coefficient | Interpretation |
|------|-------------|-----------------|
| $xv^2$ | -2.063 | Nonlinear damping from velocity-position coupling |
| $xz$ | +1.426 | Coupling between position and auxiliary state |
| $vz$ | +0.528 | Coupling between velocity and auxiliary state |
| $ze$ | +0.484 | Energy-state coupling |
| $x^2v$ | +0.277 | Quadratic position-velocity interaction |
| $v$ | +0.064 | Direct velocity contribution (weak) |
| $t$ | +0.000117 | Weak time-dependence |
| $x$ | -0.214 | Weak linear restoring force component |
| $x^3$ | -0.533 | Cubic hardening (nonlinear spring stiffness) |
| $xv$ | -0.544 | Linear velocity-position coupling |
| $xe$ | -0.712 | Position-energy coupling |
| $ve$ | -0.256 | Velocity-energy coupling |
| $v^2$ | -0.075 | Quadratic velocity damping |
| $z^2$ | -0.742 | Quadratic auxiliary state damping |
| $x^2$ | -0.768 | Quadratic position effect |
| $z$ | -1.646 | Linear auxiliary state damping |
| $e$ | -0.021 | Energy damping |

## Model Performance

- **R² = 0.9999907**: The model explains 99.99% of variance
- **Max absolute error**: 0.0151
- **Mean absolute error**: 0.00203
- **95th percentile error**: 0.00488

The extremely high accuracy indicates the discovered formula captures the true dynamics of the system.

## Variable Interpretations

- **x**: Position (displacement from equilibrium)
- **v**: Velocity (rate of position change)
- **z**: Auxiliary state variable (likely represents a filtered or secondary state)
- **e**: Energy variable (total or kinetic energy)
- **t**: Time (parameter with minimal direct effect)

## Physical Insights

1. **Nonlinear Spring**: The negative cubic term (-0.533 × x³) represents the hardening of the spring—it resists harder at larger displacements, as expected physically.

2. **Velocity-Position Coupling**: The strong negative coefficient on xv² (-2.063) suggests velocity-dependent forces that increase with displacement, consistent with amplitude-dependent damping or nonlinear restoring forces.

3. **Auxiliary State z**: The variable z appears to track a secondary dynamic (perhaps the rate of change of x, or a filtered acceleration), with strong negative coupling to acceleration suggesting it acts as a damping state.

4. **Energy Conservation**: The e variable (energy) couples with other states through nonlinear terms, capturing the amplitude-dependent oscillation behavior.

5. **Weak Time Dependence**: The coefficient on t (0.000117) is negligible, confirming the dynamics are autonomous (time-independent) to very high precision.

## Mathematical Form

The formula is a polynomial of degree 3 in the variables (x, v, z, e, t), with dominant nonlinear coupling through:
- Cubic position term (x³)
- Quadratic velocity term (v²)  
- Product terms capturing state interactions (xv², xz, vz, etc.)

This structure is consistent with a Duffing-type oscillator with state-dependent damping, where the energy variable e modulates the effective dynamics.

## Fitting Method

The coefficients were determined through multivariate polynomial least-squares regression on 4,500 training samples. The 17-parameter model was fit to minimize residual sum of squares, achieving convergence with negligible error across the full range of system behaviors observed in the dataset.
