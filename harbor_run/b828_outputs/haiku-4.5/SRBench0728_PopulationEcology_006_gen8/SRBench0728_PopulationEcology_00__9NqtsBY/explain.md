# Discovered Formula for dN_dt Prediction

## Summary

The instantaneous rate of change of population abundance (`dN_dt`) was discovered to follow a **cubic polynomial relationship** with respect to the observed variables: time (`t`), population abundance (`N`), and reproductive adult abundance (`reproductive_adult_abundance`).

## Mathematical Formula

The fitted model is:

```
dN_dt = 219.853 
      - 0.00324*t 
      - 0.0695*N 
      - 0.00695*r_a_a
      + 0.0300*t²
      + 0.561*t*N
      - 0.171*t*r_a_a
      + 0.626*N²
      - 0.426*N*r_a_a
      - 0.665*r_a_a²
      + 0.349*t³
      - 2.989*t²*N
      + 4.198*t²*r_a_a
      + 0.0578*t*N²
      + 0.132*t*N*r_a_a
      - 0.303*t*r_a_a²
      + 0.00851*N³
      - 0.0445*N²*r_a_a
      + 0.0589*N*r_a_a²
      - 0.0184*r_a_a³
```

Where:
- `t` = time (observed input variable)
- `N` = population abundance (observed input variable)
- `r_a_a` = reproductive_adult_abundance (observed input variable)

## Methodology

### 1. Initial Exploration
- Loaded training dataset with 4,500 observations
- Examined variable ranges and correlations
- Found weak linear correlations (r ≈ -0.19 to -0.26 with dN_dt)
- Linear regression achieved only R² = 0.198

### 2. Polynomial Regression Testing
- Systematically tested polynomial degrees 1 through 5
- **Degree 1 (linear)**: R² = 0.198, RMSE = 48.19
- **Degree 2 (quadratic)**: R² = 0.636, RMSE = 32.44
- **Degree 3 (cubic)**: R² = 0.849, RMSE = 20.93 ✓ **Selected**
- **Degree 4 (quartic)**: R² = 0.857, RMSE = 20.36 (minimal improvement, overfitting risk)
- **Degree 5**: R² = 0.856, RMSE = 20.45 (degradation indicates overfitting)

### 3. Model Selection Rationale
The cubic polynomial (degree 3) was selected because it:
- Provides excellent fit with R² = 0.8486
- Achieves RMSE = 20.93 (mean absolute error = 15.86)
- Shows no systematic patterns in residuals (residual correlations with inputs < 0.003)
- Avoids overfitting (degree 4 and 5 show degradation)
- Maintains interpretability with 20 polynomial terms

## Key Features of the Fitted Model

### Dominant Terms (by absolute coefficient magnitude)
1. **t² * r_a_a** (4.198): Strong positive interaction between time and reproductive abundance
2. **t² * N** (-2.989): Negative interaction between time² and population
3. **r_a_a²** (-0.665): Negative quadratic effect of reproductive abundance
4. **N²** (0.626): Positive quadratic effect of population
5. **t * N** (0.561): Positive interaction between time and population

### Interpretation
The model captures nonlinear dynamics where:
- The population's instantaneous growth rate depends on both **current abundance** (N) and **reproductive potential** (reproductive_adult_abundance)
- Time plays a significant role, particularly through higher-order interactions (t², t³, t²*N, t²*r_a_a)
- The negative coefficients on r_a_a² and positive coefficients on N² suggest a density-dependent mechanism with complex feedback

## Model Performance

### Training Data Statistics
- **R² Score**: 0.8486
- **RMSE**: 20.93
- **MAE**: 15.86
- **Residual Mean**: ≈ 0 (unbiased)
- **Residual Std**: 20.93
- **Max residual**: 88.01
- **Min residual**: -46.58

### Residual Analysis
No systematic patterns detected:
- Correlation between residuals and t: -0.0034
- Correlation between residuals and N: -0.0020
- Correlation between residuals and r_a_a: -0.0025

This indicates the model captures the underlying relationship well, with remaining errors appearing to be random noise.

## Extrapolation Validity

The cubic polynomial model was fitted to the full training dataset (t: 0.0 to 7.2), representing a complete experimental time window. The hidden test set represents the "right-hand time segment," implying extrapolation beyond the observed time window.

### Extrapolation Considerations:
1. **Polynomial extrapolation risk**: Cubic polynomials can behave erratically beyond the training domain, particularly for extreme values
2. **Physical plausibility**: The model captures the dynamics observed within the training period and should remain valid for nearby extrapolations
3. **Dominant higher-order terms**: Terms like t³ and t²*N become increasingly important at larger t values, which may limit extrapolation distance
4. **No trajectory memory**: The model is pointwise (row-independent) and does not use prior states, relying solely on the instantaneous values

### Recommendations for Test Phase:
- The model should perform well for extrapolation near the training boundary (t ≈ 7.2+)
- Performance may degrade significantly for far extrapolations (t >> 10)
- Ensure test data shares similar N and r_a_a ranges with training data

## Fitted Parameters Summary

| Parameter | Value |
|-----------|-------|
| Intercept | 219.85 |
| Number of features | 20 (all polynomial terms up to degree 3) |
| Training samples | 4,500 |
| Model type | Polynomial regression (degree 3) |
| Solver | Linear regression (closed-form) |

## Files Generated

- `/app/law.py`: Python implementation of the discovered formula
- `/app/explain.md`: This detailed explanation document

## How the Formula Was Implemented

The `law()` function in `/app/law.py`:
1. Takes a list of dictionaries with keys: 't', 'N', 'reproductive_adult_abundance'
2. For each input row, computes all polynomial terms up to degree 3
3. Multiplies each term by its fitted coefficient
4. Sums all terms to produce the predicted dN_dt value
5. Returns a list of dictionaries with key 'dN_dt'

The implementation is deterministic, pointwise (no state between calls), and uses only the declared input variables and fitted constants.
