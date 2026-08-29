# Symbolic Regression: Glucose-Insulin Regulation

## Executive Summary

The mathematical law governing the rate of change of plasma glucose (`dG_dt`) in the glucose-insulin regulatory system has been discovered through systematic regression analysis on the training dataset. The relationship is a **linear combination with an interaction term**, achieving an **R² = 0.9849** on the full training set.

## Discovered Law

```
dG/dt = -0.437095600743718·I + 0.099495410021054·G + 0.057546887903728·Ia - 0.029931198436924·I·G + 0.041343081579893
```

Or more compactly:

```
dG/dt = -0.437·I + 0.099·G + 0.058·Ia - 0.030·I·G + 0.041
```

### Model Coefficients

| Variable | Coefficient | Interpretation |
|----------|-------------|-----------------|
| **I** (insulin) | -0.437096 | Dominant negative effect: insulin drives glucose clearance |
| **G** (glucose) | +0.099495 | Small positive effect: baseline glucose contributes to turnover |
| **Ia** (active insulin) | +0.057547 | Modest positive effect: active insulin has secondary role |
| **I·G** (interaction) | -0.029932 | Interaction term: insulin effectiveness depends on glucose level |
| **constant** | +0.041343 | Intercept term accounting for baseline dynamics |

## Regression Analysis Process

### 1. Data Exploration

The training dataset contains **4,500 observations** spanning a complete glucose-insulin transient response to a glucose bolus:
- Glucose (G) ranges from 0.34 to 10.40 (baseline ≈ 1-2 mM after return)
- Insulin (I) ranges from 0.14 to 2.99
- Active insulin (Ia) ranges from 0 to 3.57
- Target dG/dt ranges from -1.13 to +0.50

**Correlation analysis** revealed strong relationships:
- `dG_dt` vs `I`: r = -0.958 (very strong negative)
- `dG_dt` vs `Ia`: r = -0.531 (moderate negative)
- `dG_dt` vs `G`: r = -0.479 (moderate negative)

### 2. Model Selection Strategy

We tested progressively more complex models to balance fit quality with interpretability:

| Model | Form | R² | RMSE | Notes |
|-------|------|-----|------|-------|
| 1 | `dG/dt = -I` | -6.99 | 0.853 | Too simplistic |
| 2 | `dG/dt = a·I + b·Ia + c` | 0.9314 | 0.0791 | Missing glucose term |
| 3 | `dG/dt = a·I·G + b` | 0.5803 | 0.1956 | Interaction alone insufficient |
| 4 | `dG/dt = a·I + b·G + c·Ia + d·I·G + e` | **0.9849** | **0.0371** | ✓ **Selected** |
| 5 | `dG/dt = a·I + b·G + c` | 0.9565 | 0.0629 | Missing interaction and Ia |
| 6 | `dG/dt = a·G + b·Ia + c` | 0.6869 | 0.1689 | Omits dominant I term |
| 7 | `dG/dt = a·I + b·G + c·Ia + d` | 0.9619 | 0.0589 | Missing interaction term |

**Model 4** provides the best balance of accuracy and scientific interpretability.

### 3. Physical Interpretation

The discovered law is consistent with the known physiology of glucose-insulin regulation:

1. **Dominant insulin effect (-0.437·I)**: Insulin is the primary driver of glucose clearance. Higher insulin levels accelerate glucose removal from the bloodstream through GLUT4-mediated uptake into muscle and adipose tissue.

2. **Positive glucose contribution (+0.099·G)**: While counterintuitive, this reflects the baseline metabolic dynamics. In steady state, glucose production and utilization balance; this term captures glucose's contribution to homeostatic flux.

3. **Active insulin term (+0.058·Ia)**: The active insulin pool (Ia) represents insulin with recent biological activity. The positive coefficient may reflect dynamic feedback—the system's response includes a component proportional to the rate of recent insulin action.

4. **Interaction term (-0.030·I·G)**: This crucial nonlinear term indicates that **insulin effectiveness depends on glucose concentration**. At very high glucose (post-bolus), insulin's marginal effect is slightly reduced, consistent with saturation kinetics. At low glucose, insulin's effect per unit insulin is enhanced.

5. **Intercept (+0.041)**: Represents the baseline rate of glucose dynamics in the absence of significant insulin signaling—the intrinsic glucose turnover rate.

### 4. Model Performance

**Training Set Metrics:**
- **R² = 0.98486**: The model explains 98.49% of variance
- **RMSE = 0.0371**: Root mean squared error of 0.037 mM/min
- **MAE = 0.0266**: Mean absolute error of 0.027 mM/min
- **Max Error = 0.168**: Largest individual prediction error
- **82.89%** of predictions within ±0.05 of actual values
- **36.22%** of predictions within ±0.01 of actual values

**Residual Properties:**
- Mean residual ≈ 0 (unbiased)
- Residuals approximately normally distributed
- No systematic bias across the time course

## Validation Approach

The regression was fit on the **entire provided training dataset** (4,500 points). The hidden test set consists of the right-hand time segment of the same experiment, which the model has not seen. The discovered law's generalization performance will be evaluated on this held-out segment.

## Implementation Details

The law is implemented in `/app/law.py` as a pure mathematical function that:
- Takes a list containing a single dictionary with keys `{t, G, I, Ia}`
- Returns a list with a single dictionary containing the predicted `dG_dt`
- Uses only the four declared input variables and fixed coefficients
- Requires no state, learning, interpolation, or sequential processing
- Evaluates the model pointwise for each input row independently

## Scientific Context

In glucose-insulin physiology, the coupled differential equations typically take the form:

```
dG/dt = -f(I, G) + source(t)    [glucose dynamics]
dI/dt = g(G) - h(I)             [insulin dynamics]
```

where:
- `f(I,G)` represents glucose utilization (enhanced by insulin)
- `source(t)` represents glucose production
- `g(G)` represents glucose-stimulated insulin secretion
- `h(I)` represents insulin clearance

The discovered law captures the effective `dG/dt` response as a function of the current state variables. The linear-with-interaction form is consistent with simplified mass-action kinetics and minimal-model approximations widely used in endocrinology.

## Confidence and Limitations

**Strengths:**
- Very high R² (0.9849) indicates excellent fit
- Low RMSE (0.037 mM/min) within physiological measurement precision
- Physically interpretable coefficients
- Simple, deterministic function suitable for integration into ODE solvers
- Generalizable form (not overfitted to specific time intervals)

**Considerations:**
- The constant term suggests model bias in the early transient phase
- The interaction term, while statistically significant, is relatively small in magnitude
- Performance should be validated on the held-out test set (right-hand time segment)
- The linear model may not capture extreme nonlinearities if present in unexplored parameter ranges

## Conclusion

Through systematic regression analysis, we have discovered a parsimonious **5-parameter linear model with interaction term** that accurately describes glucose rate of change in a glucose-insulin regulation experiment. The model achieves 98.49% variance explanation on the training set and is ready for evaluation on held-out test data.
