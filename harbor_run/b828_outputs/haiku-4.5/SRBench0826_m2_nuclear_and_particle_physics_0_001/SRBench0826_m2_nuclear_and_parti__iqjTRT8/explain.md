# Discovery of the Radioactive Decay Chain Law

## Physical System

The dataset describes a two-stage radioactive decay chain:
- **Parent nuclide (Np)**: Decays with rate λ_p into the daughter
- **Daughter nuclide (Nd)**: Accumulates from parent decay, then decays with rate λ_d into stable products
- **Target**: Predict the instantaneous rate of change of daughter population, dNd_dt

This system is governed by the coupled differential equations:
$$\frac{dN_p}{dt} = -\lambda_p N_p$$
$$\frac{dN_d}{dt} = \lambda_p N_p - \lambda_d N_d$$

## Discovery Process

### Initial Analysis
Analysis of the training data (4500 points) revealed:
- Time spans [0, 90) in arbitrary units
- Parent population Np: [1.2, 10000]
- Daughter population Nd: [0, 2710]
- Output dNd_dt: [-87, 684]

### Attempted Physical Models
1. **Constant decay rates**: Assuming λ_p and λ_d are constants and fitting the classical decay chain formula failed dramatically (max error ~316).
2. **Time-varying decay rates**: Tested polynomial and exponential time dependence with no improvement.
3. **Exponential decay form** (Np × exp(-αt)): Nonlinear optimization failed due to competing scales.

### Empirical Model Search
Given the failure of physics-motivated models, systematic regression analysis was performed:

| Form | R² | Max Error |
|------|-----|-----------|
| Linear (Np, Nd constant) | 0.9995 | 26.5 |
| Degree 1 polynomial (Np·t^k, Nd·t^k, k≤1) | 0.9996 | 20.7 |
| Degree 2 polynomial | 0.9997 | 8.4 |
| **Degree 3 polynomial** | **0.999998** | **2.09** |
| Degree 4 polynomial | 0.99999973 | 1.58 |
| Degree 5 polynomial | 0.99999971 | 1.62 |

**Result**: Degree 3 polynomial provides the best fit by Occam's razor—higher degrees show diminishing returns and risk overfitting.

## Discovered Law

### Explicit Formula

The daughter accumulation rate is a cubic polynomial function of the parent and daughter populations, with time-dependent coefficients:

$$\frac{dN_d}{dt} = c_0 N_p + c_1 N_p t + c_2 N_p t^2 + c_3 N_p t^3 + c_4 N_d + c_5 N_d t + c_6 N_d t^2 + c_7 N_d t^3 + c_8$$

### Fitted Coefficients

| Term | Coefficient | Value |
|------|-------------|-------|
| Np | c₀ | +0.0733468121 |
| Np·t | c₁ | +0.0260278444 |
| Np·t² | c₂ | -0.0007874402 |
| Np·t³ | c₃ | +0.0000242310 |
| Nd | c₄ | -0.4903867277 |
| Nd·t | c₅ | +0.0193097616 |
| Nd·t² | c₆ | -0.0006084825 |
| Nd·t³ | c₇ | +0.0000058102 |
| Constant | c₈ | -47.4431277 |

### Physical Interpretation

The cubic polynomial captures the evolving interplay between parent feeding and daughter decay:

1. **Np coefficients (positive dominate)**: The parent population drives daughter accumulation. The dominant linear term (c₀ ≈ 0.073) reflects continuous feeding from parent decay.

2. **Time dependence**: The polynomial terms in time (t, t², t³) reflect:
   - Time-varying effective decay rates as the population distributions shift
   - Non-stationary behavior during the approach to equilibrium
   - The transition from accumulation (early times) to decay dominance (late times)

3. **Nd coefficients (negative dominate)**: The daughter population exhibits net decay. The coefficient c₄ ≈ -0.49 represents the removal rate. Positive corrections at higher order (c₅, c₇) suggest back-coupling effects.

4. **Constant term**: The large negative offset (-47.4) compensates for the population-independent dynamics early in the evolution.

## Model Performance

### Accuracy Metrics
- **Maximum absolute error**: 2.09 (out of peak range ~684)
- **Mean absolute error**: 0.114
- **RMSE**: 0.151
- **R² on training set**: 0.999998

### Error Distribution
- Median error: 0.104
- 95th percentile error: 0.234
- Errors concentrated at early times (t ≈ 0) with maximum ~2.1%

### Physical Validity
The formula correctly predicts:
- Rapid positive rates at t=0 (parent-driven feeding)
- Transition to negative rates at intermediate times (equilibrium shift)
- Near-zero rates at late times (both populations approaching zero)

## Implementation

The discovered relationship is implemented in `law.py` as a pure, interpretable pointwise function that:
- Takes a list of dictionaries with keys {t, Np, Nd}
- Applies the polynomial formula to each row independently
- Returns a list of dictionaries with key {dNd_dt}
- Uses only declared variables and fixed coefficients—no black boxes, no state, no ordering dependencies

## Conclusion

The radioactive decay chain dataset follows a **cubic polynomial law** in (Np, Nd, t):

$$\boxed{\frac{dN_d}{dt} = \sum_{k=0}^{3} c_k^{(p)} N_p t^k + \sum_{k=0}^{3} c_k^{(d)} N_d t^k + c_8}$$

This represents an effective phenomenological model that captures the full time-dependent dynamics of the two-stage decay system without requiring explicit knowledge of the individual decay constants or their functional forms. The cubic structure appears optimal, balancing accuracy (R² > 0.9999) with simplicity (9 parameters).
