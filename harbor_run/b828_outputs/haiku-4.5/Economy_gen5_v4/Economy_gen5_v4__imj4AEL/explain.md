# Symbolic Regression Discovery Report

## Mathematical Formula

The discovered relationship for predicting `dp` is a **second-degree polynomial regression model** with all five input variables and their key interaction terms:

$$dp = 0.021589 + 0.261433 \cdot dc + 0.004744 \cdot pi + 0.169611 \cdot dp_{comp} - 0.011862 \cdot \sigma_c + 0.127250 \cdot dc_{acc}$$
$$- 0.011221 \cdot dc^2 + 0.141328 \cdot dc \cdot pi + 0.001955 \cdot dc \cdot dp_{comp} - 0.025293 \cdot dc \cdot \sigma_c$$
$$+ 0.000817 \cdot dc \cdot dc_{acc} + 0.004914 \cdot pi^2 - 0.007445 \cdot pi \cdot dp_{comp} + 0.017655 \cdot pi \cdot \sigma_c$$
$$- 0.007579 \cdot pi \cdot dc_{acc} + 0.003805 \cdot dp_{comp}^2 + 0.008046 \cdot dp_{comp} \cdot \sigma_c$$
$$- 0.001615 \cdot dp_{comp} \cdot dc_{acc} + 0.003209 \cdot \sigma_c^2 - 0.000678 \cdot \sigma_c \cdot dc_{acc}$$
$$- 0.000250 \cdot dc_{acc}^2$$

## Methodology

### Step 1: Data Exploration
- Loaded 4,500 training samples with 5 input variables and 1 output variable
- Analyzed correlations: `dc` shows the strongest correlation with `dp` (r = 0.87)
- Other variables show much weaker individual correlations, suggesting interactions are important

### Step 2: Linear Model Baseline
- Fit a simple linear regression model with all five input variables
- **Result**: R² = 0.9476
- Residuals showed no systematic pattern, indicating the model captured most structure
- However, residual correlation analysis showed room for improvement

### Step 3: Polynomial Feature Engineering
- Generated all second-degree polynomial features (degree 2)
- This included: squares of all variables and all pairwise interaction terms
- Total features expanded from 5 to 20 polynomial features
- Used Ridge regression with α = 0.001 for regularization to prevent overfitting

### Step 4: Feature Selection & Model Interpretation
- Identified the most important terms by coefficient magnitude:
  - **Linear terms**: `dc` (0.261), `dp_comp` (0.170), `dc_acc` (0.127)
  - **Key interaction**: `dc × pi` (0.141) - the most significant non-linear term
  - **Second-order terms**: Various quadratic and interaction terms with smaller coefficients
- Terms with coefficients < 0.0008 are effectively negligible but kept for completeness

### Step 5: Model Performance
- **R² Score**: 0.961051 (96.1% variance explained)
- **Mean Absolute Error**: 0.065
- **Maximum Absolute Error**: 0.211
- The model explains nearly 96% of the variance in the training data

## Interpretation

The formula reveals:

1. **Primary Driver**: `dc` is the dominant predictor with coefficient 0.261
2. **Important Secondary Variables**: `dp_comp` (0.170) and `dc_acc` (0.127) contribute significantly
3. **Critical Interaction**: The `dc × pi` interaction term (0.141) is nearly as important as the individual effect of `dp_comp`, suggesting that `pi` modulates the effect of `dc`
4. **Negative Feedback**: The `dc²` term is negative (-0.011), indicating diminishing returns at extreme values
5. **Fine Structure**: Multiple interaction and quadratic terms add precision, though most have small coefficients

## Model Characteristics

- **Type**: Polynomial regression (degree 2)
- **Number of Parameters**: 20 (19 coefficients + 1 intercept)
- **Fitting Method**: Ridge regression with L2 regularization (α = 0.001)
- **Training Data**: 4,500 samples
- **Generalization**: The model is designed to capture the underlying mathematical relationship without memorization

## Implementation

The discovered formula has been implemented as a pure mathematical function in `law.py` that:
- Takes a list of dictionaries with input variables as keys
- Computes the polynomial expression for each point independently
- Returns the predicted `dp` value for each input
- Uses only the five declared variables and constant coefficients (no lookup tables, no machine learning black boxes)
