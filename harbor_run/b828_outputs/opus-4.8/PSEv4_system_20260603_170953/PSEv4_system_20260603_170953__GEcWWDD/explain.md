# Discovered Law: Damped, Driven Duffing Oscillator

## Result

The instantaneous acceleration is governed by a **damped, driven Duffing oscillator**:

$$\frac{dv}{dt} = -\delta\,v \;-\; \alpha\,x \;-\; \beta\,x^3 \;+\; \gamma\,\sin(\omega t)$$

| Parameter | Symbol | Fitted value | Role |
|-----------|--------|--------------|------|
| Damping   | $\delta$ | 0.20857 | linear (viscous) damping on velocity |
| Stiffness | $\alpha$ | 0.52976 | linear restoring force |
| Nonlinear stiffness | $\beta$ | 0.84983 | cubic (hardening) restoring force |
| Forcing amplitude | $\gamma$ | 1.16908 | amplitude of periodic drive |
| Forcing frequency | $\omega$ | 0.99901 | angular frequency of the drive |

Fit quality on the training set: **R² = 0.99859**, RMSE = 0.046, max abs error = 0.16.

## How it was found

1. **Correlation screening.** `dv_dt` was strongly anti-correlated with `x` (r = −0.86) and nearly
   uncorrelated with `t` and `v` marginally — pointing to a restoring-force system.
2. **Polynomial regression.** A single term `−x³` already explained R² ≈ 0.95. Adding a linear
   `x` term (Duffing restoring force `−αx − βx³`) reached R² ≈ 0.967.
3. **Velocity damping.** Including a `−δ v` term improved the fit slightly and gave a clean
   physical interpretation.
4. **Periodic forcing.** The remaining residual correlated with `sin(t)`. Scanning the drive
   frequency $\omega$ produced a sharp optimum near $\omega \approx 1.0$ (refined to 0.99901),
   lifting the fit to R² ≈ 0.9986. A cosine (phase) component was found to be statistically
   indistinguishable from zero, so the drive is a pure sine.
5. **Nonlinear least squares.** All five parameters were refined jointly with
   `scipy.optimize.curve_fit`.

## Interpretation

This is the canonical Duffing equation, written as a first-order system for the acceleration
`dv/dt`. The state `x` experiences a nonlinear (cubic-hardening) restoring force `−αx − βx³`,
loses energy through linear damping `−δv`, and is driven by an external periodic force
`γ sin(ωt)`. The remaining residual (RMSE ≈ 0.046) is consistent with small measurement noise
and shows no further structure in `t`, `x`, or `v`.

## Implementation

`/app/law.py` evaluates the closed-form expression above for each input row independently,
using only the declared variables `t`, `x`, `v` and the five fixed constants. No data reads,
state, ordering, or numerical differentiation are used.
