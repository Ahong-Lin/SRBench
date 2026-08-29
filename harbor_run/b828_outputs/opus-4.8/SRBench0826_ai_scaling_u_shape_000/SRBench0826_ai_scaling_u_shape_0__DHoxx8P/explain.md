# Discovered law for `Brier` vs `logC`

## Summary

The data is smooth and essentially noise-free (median third finite-difference
≈ 2×10⁻⁹). The `Brier` score is a **non-monotonic** function of `logC` with:

- a shallow local minimum near `logC ≈ -2.0`,
- a pronounced local **peak** near `logC ≈ -1.0` (Brier ≈ 0.366),
- a global minimum near `logC ≈ 0.2–0.4` (Brier ≈ 0.147),
- a steady rise toward `logC = 3` (Brier ≈ 0.496), with a small wiggle.

I model it as a smooth polynomial **baseline scaling trend** plus a small number
of **localized Gaussian bumps** (interpretable as emergent / double-descent-like
localized effects):

```
Brier(logC) = P8(logC) + Σ_k A_k · exp( -(logC - μ_k)² / (2 σ_k²) )
```

where `P8` is a degree-8 polynomial in `logC`.

## Fitted form and parameters

Baseline polynomial `P8(x) = Σ c_i x^(8-i)` (Horner order, highest power first):

| power | coefficient        |
|-------|--------------------|
| x⁸    |  2.233143e-06      |
| x⁷    | -5.906642e-06      |
| x⁶    | -9.799233e-05      |
| x⁵    |  6.078135e-05      |
| x⁴    |  1.599811e-03      |
| x³    |  4.933106e-03      |
| x²    |  1.758823e-02      |
| x¹    | -6.452085e-03      |
| x⁰    |  1.467719e-01      |

Localized Gaussian terms `A · exp(-(x-μ)²/(2σ²))`:

| term | amplitude A | center μ  | width σ |
|------|-------------|-----------|---------|
| 1    | 0.199099    | -1.000279 | 0.352976 |
| 2    | 0.045630    |  1.778140 | 0.376061 |
| 3    | 0.016709    |  2.329199 | 0.348395 |

The dominant feature is Gaussian **term 1**, a bump of amplitude ≈ 0.20 centered
almost exactly at `logC = -1.0` — this is the prominent peak in the curve. Terms 2
and 3 are small, overlapping bumps on the right that capture a gentle wiggle
superimposed on the rising right-hand branch.

## Fitting method

- Loaded `/app/data/train_data.csv` (4500 rows, `logC ∈ [-3, 3]`).
- Fit all parameters simultaneously by non-linear least squares
  (`scipy.optimize.curve_fit`) with the polynomial + 3-Gaussian model above.
- Model/complexity chosen by held-out cross-validation (random 70/30 splits,
  multiple seeds): test RMSE tracks train RMSE closely (no overfitting), and the
  degree-8 baseline + 3 Gaussians was the point of clearly diminishing returns.

## Fit quality

On the full training set:

- **RMSE ≈ 2.4×10⁻⁵**
- **max absolute error ≈ 7.9×10⁻⁵**

Cross-validated test RMSE ≈ 2.4×10⁻⁵ (stable across seeds), confirming the
closed form generalizes across the observed `logC` range.

## Implementation

`/app/law.py` evaluates the polynomial via Horner's method and adds the three
Gaussian terms, mapping each input row independently to a single `Brier`
prediction. It uses only the declared variable `logC` and the fixed constants
above — no data access, interpolation, or state between calls.
