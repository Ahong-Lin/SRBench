# Velocity vs. inhibitor concentration

## Discovered law

$$v = V_f + \frac{V_0 - V_f}{1 + I/I_{50}} = 45 + \frac{325}{I + 15} = \frac{45\,I + 1000}{I + 15}$$

with fitted constants

| symbol | value | meaning |
|--------|-------|---------|
| $V_0$   | 66.6667 | velocity with no inhibitor ($I=0$) |
| $V_f$   | 45.0    | residual velocity floor as $I \to \infty$ |
| $I_{50}$| 15.0    | inhibitor concentration giving half the maximal decline |

All three forms above are algebraically identical: $325 = (V_0 - V_f)\,I_{50}$ and $1000 = V_f I_{50} + 325$.

## Fit quality

Predicting the clean target `v` on all 4500 training rows:

- **Maximum absolute error: 2.8 × 10⁻¹⁴** (machine precision — the relationship is exact).
- Against the noisy measurements `v_noisy`, RMSE ≈ 0.99, consistent with the injected measurement noise.

## Methodology

1. **Inspection.** `v` starts at 66.667 for `I = 0` and decreases monotonically as `I` grows, but it does **not** fall toward zero: at `I = 100` it is still 47.83, and the curve visibly flattens. The decline is concave-up (steep then leveling), the signature of a hyperbolic decay onto a non-zero plateau.

2. **Ruling out the naïve competitive form.** Pure competitive inhibition at fixed substrate predicts `v = C /(P + Q·I)`, i.e. `1/v` linear in `I` and `v → 0`. A linear fit of `1/v` vs `I` left residuals up to ~8.7 units, and the data plateau well above zero, so this form is rejected.

3. **Model fit.** An offset hyperbola `v = a + b/(I + c)` was fit by nonlinear least squares. It converged to `a = 45`, `b = 325`, `c = 15` with residuals at the 10⁻¹⁴ level — an exact match. An equivalent parameterization `v = Vf + (V0−Vf)/(1 + I/I50)` gives the interpretable constants in the table.

## Biological interpretation

This is **partial (hyperbolic) inhibition**. As the reversible inhibitor is titrated in at fixed substrate, the apparent catalytic velocity falls along a rectangular hyperbola in `I`. Rather than driving activity to zero, it drives it toward a non-zero floor `V_f = 45`: the enzyme–inhibitor complex retains partial turnover (or an inhibitor-insensitive pathway persists). The parameter `I50 = 15` is the inhibitor concentration at which velocity has dropped halfway from `V0 = 66.67` to the floor `V_f = 45` (i.e. to ≈55.83). The total achievable suppression is `V0 − V_f = 21.67` velocity units.

## Implementation

`/app/law.py` evaluates `v = 45 + 325/(I + 15)` for each row independently — a pure, pointwise closed-form expression in the single input variable `I` with fixed constants, no state or data access.
