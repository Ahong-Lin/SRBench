# Discovered Mathematical Law: Seasonally Forced SIR Model

## Executive Summary

The experimental dataset reveals a **modified SIR (Susceptible-Infected-Recovered) epidemiological model with sinusoidal seasonal forcing** governing the rate of change of infectious individuals. The model captures yearly environmental cycles that modulate disease transmissibility, producing recurrent epidemic waves with consistent period and amplitude.

## Mathematical Form

$$\frac{dI}{dt} = c_0 + c_S S + c_I I + c_{SI} S I + c_{SI}^{\cos} S I \cos(2\pi t) + c_{SI}^{\sin} S I \sin(2\pi t) + c_I^{\cos} I \cos(2\pi t) + c_I^{\sin} I \sin(2\pi t)$$

### Fitted Parameters

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| $c_0$ | 0.0997 | Baseline constant term (residual dynamics) |
| $c_S$ | -0.0931 | Weak S-dependence (higher when S decreases) |
| $c_I$ | -6.173 | Recovery rate coefficient (loss of infectivity) |
| $c_{SI}$ | 10.207 | Baseline transmission rate ($\beta_0 S I$) |
| $c_{SI}^{\cos}$ | 0.844 | Amplitude of seasonal forcing on transmission (cosine component) |
| $c_{SI}^{\sin}$ | -0.187 | Amplitude of seasonal forcing on transmission (sine component) |
| $c_I^{\cos}$ | 0.0325 | Weak seasonal modulation of recovery (cosine) |
| $c_I^{\sin}$ | 0.1395 | Weak seasonal modulation of recovery (sine) |

## Physical Interpretation

### Core SIR Dynamics
The dominant terms follow standard SIR formulation:
$$\frac{dI}{dt} \approx c_{SI} S I - c_I I$$

where:
- **$c_{SI} S I$ term**: Newly infected individuals per unit time (mass action principle)
  - Proportional to product of susceptible and infectious fractions
  - Baseline transmission rate coefficient: $\beta_0 = 10.207$ per year
  
- **$-c_I I$ term**: Loss of infectivity through recovery
  - Recovery rate: $\gamma = 6.173$ per year
  - Average infectious period: $\approx 1/6.173 \approx 0.162$ years $\approx 59$ days

### Seasonal Environmental Forcing

The seasonal terms capture **yearly (annual) environmental cycles** affecting disease transmissibility:

$$\Delta\beta(t) = A \cos(2\pi t + \phi)$$

where:
- **Frequency**: $\omega = 2\pi$ rad/year (period = 1 year)
- **Seasonal amplitude**: $A = \sqrt{(0.844)^2 + (-0.187)^2} = 0.865$
- **Phase shift**: $\phi = \arctan(-0.187/0.844) = -12.5°$ 

This represents transmission rate modulation of approximately **8.5%** around the baseline, consistent with:
- Temperature-dependent disease survival
- Host behavior changes (school calendars, social mixing)
- Immune system seasonal variation

### Minor Terms
- **Constant term** ($c_0 = 0.0997$): Small baseline offset, likely represents boundary effects or numerical coupling
- **S-dependent term** ($c_S = -0.0931$): Weak second-order effect on transmission dynamics
- **Recovery seasonality** ($c_I^{\cos}, c_I^{\sin}$): Minimal modulation of recovery rate, indicating recovery is relatively stable year-round

## Model Properties

### Validation Metrics
- **RMSE**: $3.83 \times 10^{-4}$ (excellent fit)
- **$R^2$**: 0.9996 (explains 99.96% of variance)
- **Max prediction error**: $0.00106$
- **Mean absolute error**: $0.000317$

### Epidemic Characteristics
The model predicts:
- **Baseline reproductive number** (at S ≈ 0.5): $R_0 \approx 1.66$ (endemic transmission)
- **Recurrent epidemic period**: 1 year (driven by seasonal forcing)
- **Oscillation pattern**: Quasi-sinusoidal waves with stable amplitude maintained by the periodic forcing
- **Amplitude**: Approximately 0.07 (7% of population) for I variations

## Biological Context

This model is characteristic of **childhood infectious diseases** with strong seasonal forcing:
- Measles, pertussis, influenza - diseases with primarily respiratory transmission affected by environmental conditions
- The ~0.16 year (59 day) infectious period matches observed durations for these pathogens
- The annual forcing frequency matches school calendars and seasonal immune system effects

## Assumptions and Limitations

1. **Pointwise independence**: Model predicts $dI/dt$ from current state only (no trajectory memory)
2. **Constant population**: Total population conserved ($S + I + R \approx$ constant)
3. **Homogeneous mixing**: No spatial or age structure
4. **Known parameters**: $C$ (cumulative cases) included in feature set but not used in final model
5. **Continuous approximation**: Valid for large population sizes
6. **Fixed seasonal frequency**: Annual cycle is rigid, not data-adaptive

## Epidemiological Insight

The discovery of strong seasonal forcing with **phase-lagged transmission modulation** (-12.5° phase shift) suggests the mechanism is not purely temperature-driven (which would align with time) but involves **cultural/behavioral factors** (school terms) that lead environmental conditions. The small recovery rate seasonality (vs. large transmission seasonality) indicates **host recovery is intrinsic**, while **transmission depends on environmental contacts**.

The model captures the fundamental insight from the problem context: **periodic environmental forcing combined with constant recovery rates sustains epidemic oscillations** without boom-bust extinction, maintaining a quasi-endemic steady state of recurrent waves.
