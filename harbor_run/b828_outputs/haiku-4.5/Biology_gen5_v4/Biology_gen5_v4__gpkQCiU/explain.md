# Discovered Mathematical Relationship

## Formula

The discovered law relating the output variable `X` to input variables `t` and `I_light_prev` is:

$$X = 0.7669 \cdot \sin(0.2625 \cdot t) + 0.0017 \cdot I_{\text{light\_prev}} + 0.5247 \cdot \sin(0.2625 \cdot t) \cdot I_{\text{light\_prev}} - 0.00063$$

Or equivalently:

$$X = \sin(0.2625 \cdot t) \cdot [0.7669 + 0.5247 \cdot I_{\text{light\_prev}}] + 0.0017 \cdot I_{\text{light\_prev}} - 0.00063$$

This form reveals that light intensity **modulates the amplitude** of the sinusoidal oscillation.

## Methodology

### 1. Initial Exploration
- Examined correlation coefficients between individual variables and `X`
- Direct linear correlations with `t` (-0.056) and `I_light_prev` (0.025) were weak
- This suggested a non-linear relationship, particularly sinusoidal behavior

### 2. Frequency Optimization
- Hypothesized a sinusoidal relationship: `X ~ sin(f*t)` where `f` is the frequency
- Systematically searched for the frequency that maximized correlation with `X`
- Coarse search identified a frequency around 0.26
- Fine-tuned using scipy.optimize.minimize to find the optimal frequency: **0.26253555**

### 3. Interaction Term Discovery
- Initial linear model with `[sin(f*t), I_light_prev]` gave R² = 0.8780
- Testing revealed that an **interaction term** `sin(f*t) * I_light_prev` significantly improves fit
- The interaction term coefficient is large (0.5247), indicating strong modulation of oscillation amplitude by light intensity

### 4. Final Model Validation
- **R² Score**: 0.9269 (explains 92.7% of variance in training data)
- **RMSE**: 0.2634
- **MAE**: 0.2222
- **Improvement over initial model**: +5% in R², -23% in error metrics

## Key Parameters

| Parameter | Value | Interpretation |
|-----------|-------|-----------------|
| Frequency | 0.26253555 | Controls oscillation period (period ≈ 24 time units) |
| Base sin coefficient | 0.76688731 | Base amplitude of sinusoidal component |
| I_light linear term | 0.00170049 | Minor direct linear contribution |
| Interaction coefficient | 0.52468886 | **Light-dependent amplitude modulation** |
| Intercept | -0.00063492 | Minimal vertical shift |

## Biological Context

The discovered model reveals a **light-modulated circadian rhythm**:

1. **Temporal Oscillation**: The sinusoidal component with frequency 0.2625 corresponds to a wavelength of ~24 time units, characteristic of circadian (daily) biological rhythms

2. **Light Modulation**: The large interaction term coefficient (0.5247) indicates that previous light intensity significantly modulates the amplitude of the rhythm:
   - When `I_light_prev` = 0: oscillation has base amplitude of 0.767
   - When `I_light_prev` = 1: oscillation amplitude becomes 0.767 + 0.525 = 1.292
   - When `I_light_prev` = 2: oscillation amplitude becomes 0.767 + 1.049 = 1.816

3. **Biological Interpretation**: This pattern is consistent with organisms whose circadian rhythms respond to light:
   - The internal clock (sinusoidal term) drives the baseline rhythm
   - External light conditions modulate the **amplitude** of this rhythm
   - This is observed in photosynthesis, melatonin production, and circadian gene expression

## Performance Summary

- **R² Score**: 0.9269 (92.7% of variance explained)
- **RMSE**: 0.2634
- **MAE**: 0.2222
- **Method**: Frequency optimization → interaction term discovery → linear regression
- **Interpretability**: Fully interpretable mathematical formula with clear biological meaning
