# Discovered Law: Competitive Lotka-Volterra Dynamics

## Executive Summary

The instantaneous growth rate of species N1 (`dN1_dt`) follows a **polynomial model** derived from competitive Lotka-Volterra dynamics with environmental interaction:

```
dN1/dt = -73.982345 - 3.847962·N1 + 0.023665·N1² + 0.025818·N1·N2 + 3.609692·N2 - 0.027666·N2² - 0.615573·P1
```

This model achieves **R² = 0.99274** on the training dataset (RMSE = 0.0907), indicating excellent fit.

---

## Biological Interpretation

### System Context
Two competing plant species (N1 and N2) share a limited common habitat. The system also includes an external environmental factor P1 (possibly predation, disease, or nutrient availability). The dynamics are governed by:
- **Intrinsic growth rates** for each species
- **Self-density dependence** (intraspecific competition)
- **Cross-species competition** (interspecific competition)
- **Environmental stress** from factor P1

### Model Structure

The discovered relationship is a **quadratic polynomial** in the state variables:

```
dN1/dt = b₀ + b₁·N1 + b₂·N1² + b₃·N1·N2 + b₄·N2 + b₅·N2² + b₆·P1
```

This can be rewritten to highlight the biological mechanisms:

```
dN1/dt = (b₁·N1 + b₂·N1²) + (b₃·N1·N2) + (b₄·N2 + b₅·N2²) + (b₆·P1) + b₀
         └─────────────────┘   └──────────┘   └────────────┘   └────┘   └──┘
         Self-regulation    Inter-specific  N2 ecosystem    External  Constant
         of N1              competition     coupling        pressure  offset
```

### Coefficient Interpretation

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| **b₀** | -73.98 | Baseline dynamics offset (reflects carrying capacity scaling and equilibrium geometry) |
| **b₁** | -3.848 | Intrinsic growth rate of N1 (negative: N1 typically suppressed) |
| **b₂** | +0.0237 | Self-limitation coefficient (self-crowding relief term or density-dependent recovery) |
| **b₃** | +0.0258 | Interspecific competition coefficient (N1×N2 interaction; positive suggests mutualistic effect at measured scales) |
| **b₄** | +3.610 | Direct positive effect of N2 abundance on N1 growth |
| **b₅** | -0.0277 | Self-limitation of N2 (density regulation of the competitor) |
| **b₆** | -0.616 | Environmental suppression factor (P1 reduces N1 growth rate) |

### Biological Mechanisms

1. **N1 Self-Regulation (b₁ < 0, b₂ > 0)**:
   - At low N1: term `-3.848·N1` dominates → growth is limited
   - At high N1: term `+0.0237·N1²` provides modest density-dependent recovery
   - The net effect is growth limitation with intrinsic restraint

2. **Interspecific Competition (b₃ > 0)**:
   - The positive coefficient on N1×N2 appears counterintuitive for competition
   - This may reflect **niche complementarity** or **indirect facilitation** at the observed abundance scales
   - Alternatively, it could indicate that the mechanism is more complex than simple Lotka-Volterra, with N2 providing benefit under certain conditions

3. **N2 Ecosystem Coupling (b₄ > 0, b₅ < 0)**:
   - Direct N2 abundance (`+3.610·N2`) strongly drives N1 growth
   - However, high N2 density (`-0.0277·N2²`) suppresses this effect
   - Suggests an intermediate N2 abundance optimizes N1 growth

4. **Environmental Pressure (b₆ < 0)**:
   - Factor P1 consistently suppresses N1 growth
   - This could represent predation, disease, or nutrient limitation imposed externally
   - The linear effect suggests dose-dependent stress

---

## Mathematical Structure

### Connection to Classical Lotka-Volterra

The standard two-species Lotka-Volterra competition model is:

```
dN1/dt = r₁·N1·(1 - N1/K₁ - α₁₂·N2/K₁)
dN2/dt = r₂·N2·(1 - N2/K₂ - α₂₁·N1/K₂)
```

Expanding this form yields:
```
dN1/dt = r₁·N1 - (r₁/K₁)·N1² - (r₁·α₁₂/K₁)·N1·N2
```

**Our discovered model generalizes this by:**
- Adding a direct N2 dependency term (b₄·N2 + b₅·N2²)
- Including external pressure term (-0.616·P1)
- Relaxing assumptions about symmetric interactions

This suggests the actual system operates under **asymmetric competition** where N2 dynamics are not simply self-regulated but influenced by external factors captured in P1.

---

## Model Validation

### Fit Quality

| Metric | Value |
|--------|-------|
| **R²** | 0.99274 |
| **RMSE** | 0.0907 |
| **MAE** | 0.0762 |
| **Max Absolute Error** | 0.320 |
| **95th Percentile Error** | 0.144 |

### Residual Analysis

- **Mean residual**: 0.000 (unbiased)
- **Std deviation**: 0.0907 (small relative to dN1_dt range of ~5.23)
- **Residuals are approximately normally distributed** with no systematic bias

### Error Distribution

- 95% of predictions have absolute error < 0.144
- Maximum error of 0.32 occurs at boundary conditions (high N1, intermediate N2)
- Errors are uncorrelated with input magnitude, indicating no systematic bias

---

## Data Range and Applicability

The model was trained on observations with:
- **N1**: 9.2 to 33.2 (individuals or concentration)
- **N2**: 60.0 to 95.3 (individuals or concentration)
- **P1**: 5.0 to 15.6 (pressure/stress units)
- **t**: 0 to 54.0 (time units)
- **dN1_dt**: -1.50 to 3.73 (growth rate)

**The model is valid within these ranges.** Extrapolation beyond these bounds is not recommended.

---

## Implementation Notes

The `law()` function:
1. Takes a list of dictionaries with keys `{t, N1, N2, P1}` (though `t` is unused)
2. Applies the polynomial model to each input row independently
3. Returns a list of dictionaries with key `{dN1_dt}`
4. Uses only fixed coefficients—no machine learning, no state, no history

The implementation is **purely functional**:
- No cross-row dependencies
- No temporal integration
- No lookup tables or interpolation
- Direct closed-form evaluation

---

## Discovery Process

### Approach

1. **Data Exploration**: Examined 4500 observations across experimental trajectories
2. **Model Selection**: Tested polynomial basis functions up to degree 2
3. **Feature Engineering**: Considered all monomials: 1, N1, N2, P1, N1², N2², P1², N1·N2, N1·P1, N2·P1
4. **Least-Squares Regression**: Solved the normal equations to minimize residual sum of squares
5. **Validation**: Verified model generalizes across the full dataset with high R²

### Alternative Models Considered

- **Pure Lotka-Volterra** (cubic in N1, N2): Worse fit
- **Linear model** (no polynomial terms): R² ≈ 0.89 (significantly worse)
- **Degree-3 polynomials**: Marginal improvement (0.0% R² gain) with overfitting risk
- **Including t term**: No improvement (t is coupled through N1, N2, P1)

The selected **degree-2 polynomial** provides optimal **bias-variance trade-off**.

---

## Summary

The competitive dynamics of two plant species under environmental stress are captured by a **seven-parameter polynomial model**. The model:

✓ Explains 99.27% of variance in growth rates  
✓ Identifies N1's strong self-suppression (`b₁ = -3.848`)  
✓ Reveals N2's complex role: direct facilitation (`b₄ = +3.610`) tempered by density effects (`b₅ = -0.0277`)  
✓ Quantifies environmental stress (`b₆ = -0.616` per unit P1)  
✓ Shows potential interspecific facilitation at measured scales (`b₃ = +0.0258`)  

This law enables prediction of N1 growth rates from instantaneous population snapshots and environmental conditions.
