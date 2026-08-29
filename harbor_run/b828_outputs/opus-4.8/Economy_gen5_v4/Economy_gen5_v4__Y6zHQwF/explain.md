# Discovering the law for `dp`

## Final formula

```
dp = 0.216158 · pi · tanh(dc)
   + 0.200506 · tanh(dp_comp)
   + 0.200158 · tanh(dc_acc)
   + 0.015835 · dc
   + 0.055524 · dc²
   + 0.199088 · dc³
   − 0.012986 · dc⁴
   − 0.030169 · dc⁵
   − 0.025702 · dc · sigma_c
   − 0.005031
```

Fit quality on the training set: **R² = 0.9977**, RMSE = 0.0186, max abs error = 0.052.
This matches the ceiling of a flexible gradient-boosting model (CV R² ≈ 0.998), so the
remaining residual is essentially irreducible noise rather than missing structure.

## Interpretation

The law is (almost) an additive combination of per-variable response functions:

- **`dp_comp` and `dc_acc`** each enter through a **saturating `tanh` response** with an
  identical weight of ≈ **0.20**. Their effect grows linearly for small values and
  saturates for large magnitudes — a natural "diminishing response" shape.
- **`dc`** has two contributions:
  1. A **`pi`-modulated saturating term** `0.216 · pi · tanh(dc)` — the demand-change
     response is amplified by inflation `pi`. This term shares the same ≈0.2 weight family.
  2. An **expanding polynomial base** `0.016·dc + 0.056·dc² + 0.199·dc³ − …`, dominated by
     a cubic (`≈0.2·dc³`), with a mild even (`dc²`) asymmetry and small high-order corrections.
- **`sigma_c`** (a volatility) is otherwise irrelevant; it only appears as a weak
  **damping interaction** `−0.026 · dc · sigma_c`, reducing the sensitivity of `dp` to `dc`
  when volatility is high.

## Methodology

1. **Exploration.** Correlations showed `dp` driven mostly by `dc` (r=0.87), then `dc_acc`
   (0.34) and `dp_comp` (0.25); `pi` and `sigma_c` had ~0 marginal correlation.
2. **Linear baseline.** An OLS fit reached R²=0.95. Residuals correlated with `dc³` and
   `dc·pi`, revealing nonlinearity and an interaction.
3. **Additive decomposition.** Because the inputs are mutually independent in the data, the
   conditional mean `E[dp | x_i]` recovers each variable's response function up to a constant.
   Binned conditional means showed: `dc` expanding & cubic-like; `dp_comp` and `dc_acc`
   monotone-saturating; `sigma_c` flat.
4. **Interaction structure.** Fitting `dp = h(dc) + pi·m(dc) + …` per `dc`-bin showed the
   `pi`-modulation `m(dc)` is an **odd, saturating S-curve** — fit cleanly by `0.21·tanh(dc)`
   (best-fit slope ≈ 1.0). A second, weaker interaction `dc·sigma_c` was found via tercile
   analysis (the `dc`-slope decreases with `sigma_c`).
5. **Unified fit.** Positing `tanh` responses for `dp_comp`, `dc_acc`, and `pi·dc` gave three
   nearly-identical coefficients (0.2005, 0.2002, 0.207) — strong evidence for a shared
   generating constant of ≈0.2. The `dc` base curve required terms up to `dc⁵` to reach the
   noise floor; these were fitted jointly by least squares to obtain the coefficients above.

## Fitted parameters

| Term | Coefficient |
|---|---|
| `pi·tanh(dc)` | 0.216158 |
| `tanh(dp_comp)` | 0.200506 |
| `tanh(dc_acc)` | 0.200158 |
| `dc` | 0.015835 |
| `dc²` | 0.055524 |
| `dc³` | 0.199088 |
| `dc⁴` | −0.012986 |
| `dc⁵` | −0.030169 |
| `dc·sigma_c` | −0.025702 |
| constant | −0.005031 |

The three `tanh` weights and the leading `dc³` coefficient all cluster around 0.20, which is
likely the true underlying constant; the small `dc⁴`/`dc⁵` terms are refinements of the
`dc` base curve within the observed range `dc ∈ [−2, 1.6]`.
