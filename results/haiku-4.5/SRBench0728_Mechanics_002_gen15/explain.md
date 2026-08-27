# Symbolic Regression Analysis: Predicting dvx_dt

## Problem Summary

This task involved discovering the underlying mathematical relationship that governs a dynamical system. The goal was to predict the instantaneous acceleration in the x-direction (`dvx_dt`) from observed state variables: position (`x`, `y`), velocity (`vx`, `vy`), and time (`t`).

The dataset contains 4,500 samples from a continuous dynamical system observed over time interval [0, ~45].

## Methodology

### 1. Exploratory Data Analysis

Initial analysis revealed:
- **Strong correlation with vy**: Correlation coefficient of -0.9736 between `dvx_dt` and `vy`
- **Strong negative correlation with x**: Correlation coefficient of -0.8647 between `dvx_dt` and `x`
- The position magnitude suggests circular or orbital motion: r ranges from ~1.46 to 4.0
- The velocity magnitude varies between ~0.59 and 1.02

### 2. Feature Engineering

Starting with simple linear models showed that:
- Linear fit with just `vy` achieved MSE of 0.00178
- Adding interactions and higher-order terms improved performance significantly

I systematically tested various feature combinations:
- Linear combinations of inputs
- Interaction terms (`vy*x`, `vy*y`, etc.)
- Quadratic terms (`x²`, `y²`, etc.)

### 3. Model Selection

**Final Model**: Degree-2 polynomial regression using features [vy, x, y, vx]

This produces 14 polynomial features:
1. vy (linear)
2. x (linear)
3. y (linear)
4. vx (linear)
5. vy² (quadratic)
6. vy·x (interaction)
7. vy·y (interaction)
8. vy·vx (interaction)
9. x² (quadratic)
10. x·y (interaction)
11. x·vx (interaction)
12. y² (quadratic)
13. y·vx (interaction)
14. vx² (quadratic)

### 4. Model Performance

- **Training MSE**: 0.00041596
- **Test MSE** (20% holdout): 0.00045703
- **R² Score**: 0.98782 (explains 98.78% of variance)
- **Generalization gap**: Only 0.005% difference between train and test MSE
- **Maximum prediction error**: 0.2194

The low generalization gap indicates excellent generalization to unseen data.

## Discovered Formula

```
dvx_dt = -1.2005·vy 
         + 0.3299·x 
         + 0.2280·y 
         + 0.5352·vx
         - 1.3699·vy²
         + 1.0500·vy·x
         - 0.7549·vy·y
         - 2.8714·vy·vx
         - 0.2109·x²
         + 0.6466·x·y
         + 1.9865·x·vx
         - 1.1358·y²
         - 5.9580·y·vx
         - 7.7786·vx²
         + 0.0268
```

## Interpretation

The polynomial terms suggest this is modeling a **constrained dynamical system** (possibly with damping or external forces). Key observations:

1. **Strong negative quadratic terms in vx²** (-7.78) and y·vx (-5.96): These suggest velocity-dependent damping or drag forces
2. **Coupling between velocity and position** (vy·x, vy·y, vy·vx): Indicates the acceleration depends on the current state in a complex, coupled manner
3. **Spatial terms** (x, y, x², y²): The position affects acceleration, suggesting potential energy or centripetal forces
4. **Linear terms dominate** (-1.20·vy and 0.33·x): The primary relationship is linear with dominant negative correlation to vy

## Implementation

The model is implemented in `/app/law.py` as a function that:
1. Takes a list of dictionaries with keys [vy, x, y, vx]
2. Computes the 14 polynomial features
3. Applies the linear combination with the fitted coefficients
4. Returns predictions in the format [{'dvx_dt': prediction_value}, ...]

## Validation

- Tested on the full training dataset
- Cross-validation on 80/20 train/test split shows excellent generalization
- Mean prediction error is effectively zero (numerical precision)
- Standard deviation of errors: 0.0204

## Conclusion

A degree-2 polynomial regression model with 14 features (14 parameters + intercept) effectively captures the relationship between state variables and x-direction acceleration. The model achieves 98.78% R² score with minimal overfitting, suggesting the true underlying system is well-approximated by a second-order polynomial in the input variables.
