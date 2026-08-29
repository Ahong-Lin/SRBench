# Discovering the law for `dp`

## Summary of the discovered formula

$$
\widehat{dp} = P(dc,\pi)\;+\;0.2005\,\tanh(dp_{comp})\;+\;0.2003\,\tanh(dc_{acc})\;-\;0.0258\,(dc\cdot\sigma_c)\;-\;0.0049
$$

where the consumption/inflation core is a low‑order polynomial in `dc` modulated by `pi` (`π`):

$$
P(dc,\pi) = 0.0179\,dc + 0.2419\,dc\,\pi - 0.0578\,dc\,\pi^2
+ 0.0514\,dc^2 + 0.1855\,dc^3 - 0.0127\,dc^4 - 0.0274\,dc^5
+ 0.0071\,dc^2\pi - 0.0195\,dc^3\pi .
$$

On the training set this achieves **R² = 0.9980**, residual std **0.0173**, max abs error **0.067**. Five‑fold cross‑validation gives the same residual (0.0173), which equals the noise floor found by a gradient‑boosting model — i.e. the formula captures essentially all the deterministic structure in the data.

## Methodology

1. **Screening.** A plain linear fit already gave R² = 0.95, with `dc` dominating and `pi`, `sigma_c` near‑zero *linear* coefficients. A random forest confirmed the importance ranking `dc` (0.80) ≫ `dc_acc` (0.13) > `dp_comp` (0.06) ≫ `pi`, `sigma_c`. Gradient boosting reached residual ≈ 0.017, telling me the true relation is smooth and (almost) noise‑free, so a closed form should exist.

2. **Component isolation.** By selecting rows where two of the three "secondary" drivers were near zero, I isolated each variable's marginal effect:
   - **`dp_comp`**: an odd, *saturating* effect — contribution ≈ ±0.15 at `dp_comp = ±1`, with a slope near the origin larger than the saturated value. This is exactly `0.2·tanh(dp_comp)`.
   - **`dc_acc`**: same shape, saturating near ±0.20 at `dc_acc ≈ ±2`. This is `0.2·tanh(dc_acc)`.
   - When fit jointly and freely, both coefficients came out at **0.2005** and **0.2003** with `tanh` gains of **0.997** and **0.982** — a striking symmetry that strongly suggests the true terms are `0.2·tanh(dp_comp)` and `0.2·tanh(dc_acc)`.

3. **Core `dc`–`pi` term.** After subtracting the two `tanh` terms, the remainder `z` depends on `dc` and `pi`. It is odd‑ish and *super‑linear* in `dc` (grows like a cubic, does not saturate), and its magnitude increases with `pi` (i.e. `pi` acts as a gain). Writing `z = f_0(dc) + π·f_1(dc)` revealed a pi‑independent cubic‑like growth plus a pi‑proportional term. A compact polynomial `P(dc,π)` with terms up to `dc^5` and `dc·π`, `dc·π²`, `dc²·π`, `dc³·π` reproduces this down to the noise floor.

4. **Small correction.** The residual still correlated weakly with `dc·sigma_c`; adding that single term (`sigma_c` otherwise has no effect) removed it. `sigma_c` is therefore only a minor multiplicative modulation of the `dc` effect.

5. **Validation.** Coefficients are ordinary least squares on the full training set. 5‑fold CV residual (0.0173) matches the in‑sample residual and the model‑agnostic noise floor, confirming the fit generalizes rather than overfits.

## Interpretation

- `dc` (with `pi` as a gain) is the primary driver of `dp`, entering as an expansive polynomial.
- `dp_comp` and `dc_acc` each add a **bounded** `0.2·tanh(·)` contribution — near‑linear for small values, saturating for large ones — and enter with identical magnitude.
- `sigma_c` only slightly scales the `dc` response; `pi` matters chiefly through its interaction with `dc`.

## Fitted parameters

| term | coefficient |
|------|-------------|
| `dc` | 0.01786 |
| `dc·pi` | 0.24189 |
| `dc·pi²` | -0.05776 |
| `dc²` | 0.05138 |
| `dc³` | 0.18546 |
| `dc⁴` | -0.01271 |
| `dc⁵` | -0.02741 |
| `dc²·pi` | 0.00715 |
| `dc³·pi` | -0.01946 |
| `tanh(dp_comp)` | 0.20050 |
| `tanh(dc_acc)` | 0.20031 |
| `dc·sigma_c` | -0.02576 |
| intercept | -0.00489 |
