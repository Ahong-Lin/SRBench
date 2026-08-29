# Discovering the law for `dp`

## Summary of the discovered formula

$$
dp = a\,dc + a_2\,dc^2 + b\,dc^3 \;+\; c\,dc\cdot pi + h\,pi \;+\; d\,\sin(k_1\,dp\_comp) \;+\; e\,\sin(k_2\,dc\_acc) \;+\; j\,dc\cdot sigma\_c \;+\; g
$$

with fitted parameters

| symbol | value | role |
|--------|-------|------|
| `a`  | 0.121265 | linear own-signal (`dc`) |
| `a2` | 0.035448 | quadratic (`dc²`) asymmetry |
| `b`  | 0.076135 | cubic (`dc³`) growth |
| `c`  | 0.141139 | `dc·pi` interaction |
| `d`  | 0.164007 | competitor pass-through amplitude |
| `k1` | 1.196588 | competitor saturation rate |
| `e`  | 0.189990 | acceleration amplitude |
| `k2` | 0.932040 | acceleration saturation rate |
| `h`  | 0.017858 | linear `pi` |
| `j`  | -0.023660 | `dc·sigma_c` interaction |
| `g`  | -0.012698 | offset |

On the full training set this gives **R² = 0.9938**, **RMSE = 0.0304**.

## Methodology

1. **Correlation screen.** `dp` correlates most strongly with `dc` (0.87), then `dc_acc` (0.34) and `dp_comp` (0.25). `pi` and `sigma_c` showed near-zero marginal correlation. A plain linear fit already reached R² ≈ 0.95, with `dc`, `dp_comp`, `dc_acc` dominant.

2. **Interaction search.** Adding pairwise products, only `dc·pi` stood out (coefficient ≈ 0.14), revealing that `pi` acts as a multiplier on `dc` rather than additively.

3. **Marginal shape analysis.** Because the inputs are mutually independent, I estimated each variable's marginal effect by binning:
   - `dc`: monotone and slightly asymmetric — well described by a cubic `a·dc + a2·dc² + b·dc³`.
   - `dp_comp`: monotone increasing but **saturating** at the extremes → a sine `d·sin(k1·dp_comp)`.
   - `dc_acc`: strongly **saturating and turning over** near |dc_acc|≈1.6 → a sine `e·sin(k2·dc_acc)`. A bounded sine is preferable to a polynomial for extrapolation here.
   - `sigma_c`: essentially flat marginally, but its residual showed a small `dc·sigma_c` interaction.
   - `pi`: a small residual linear `pi` term beyond the `dc·pi` interaction.

4. **Nonlinear fit.** Parameters were fitted with `scipy.optimize.curve_fit`. A 70/30 hold-out confirmed the two small terms (`h·pi`, `j·dc·sigma_c`) improve out-of-sample R² (0.9940 vs 0.9936), so they were retained. The final parameters are fit on all data.

5. **Residuals.** The remaining residual (σ ≈ 0.030) is homoscedastic — its magnitude is independent of `sigma_c` and every other input — consistent with irreducible measurement noise rather than missing structure.

## Interpretation

The response is driven mainly by the own signal `dc` (a mildly asymmetric cubic), amplified by the weight/inflation term `pi` through the `dc·pi` interaction. Competitor movement (`dp_comp`) and the acceleration term (`dc_acc`) enter with a **saturating** (sine) pass-through, so large shocks have diminishing marginal impact. `sigma_c` contributes only a weak damping interaction with `dc`.
