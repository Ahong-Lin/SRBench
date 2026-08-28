# Discovered law: Brier score vs. log-compute

## Summary

The data (`logC` ∈ [−3, 3], `Brier` ∈ [0.147, 0.496]) is essentially **noise-free**
(median second difference ≈ 3×10⁻⁷). The relationship is non-monotonic:

- a shallow, roughly-linear decrease from `logC = −3` down to a local minimum near `logC ≈ −1.9`,
- a large, sharp **bump** peaking at `logC ≈ −1.0` (Brier ≈ 0.37),
- a drop to the **global minimum** near `logC ≈ 0.25` (Brier ≈ 0.147),
- an accelerating rise on the high-compute side up to Brier ≈ 0.50 at `logC = 3`, carrying
  smaller localized features around `logC ≈ 1.75` and `≈ 2.3`.

## Functional form

I decompose the curve into a **smooth compute-scaling baseline** plus a small number of
**localized Gaussian effects** (matching the problem hint: "smooth transitions or localized effects"):

```
Brier(logC) = c + A·exp(k·logC) + B·logC
              + Σ_i  G_i · exp( −(logC − μ_i)² / (2·σ_i²) )
```

**Why this form.** After isolating the dominant peak (by fitting a smoothing-spline
baseline through the data *outside* the peak window and subtracting it), the residual was a
clean symmetric Gaussian centred at `logC ≈ −1.0` with amplitude ≈ 0.199 and σ ≈ 0.353
(≈ 1/(2√2), i.e. `≈ 0.20·exp(−4·(logC+1)²)`). The remaining smooth part is a valley that is
nearly **linear** on the low-compute side (slope ≈ −0.053, constant over [−3, −2]) but
**accelerates like an exponential** on the high-compute side — captured by
`c + A·exp(k·logC) + B·logC`. Two further small, localized Gaussian bumps on the
high-compute side (plus one tiny broad correction) account for the mild oscillation left in
the residuals.

Pure polynomials fit poorly (degree-10 RMSE ≈ 0.015) precisely because of the sharp
localized peak — confirming the "baseline + Gaussian bump" decomposition rather than a
global polynomial.

## Fitting method

- Loaded with `pandas.read_csv`, sorted by `logC`.
- Fit by non-linear least squares (`scipy.optimize.curve_fit`) on the full training set.
  Initial guesses were built up progressively: the main Gaussian from the spline-residual
  analysis, the exp+linear baseline from the bump-subtracted data, and the small
  high-compute Gaussians from the remaining residual structure.
- Validated with a 70/30 random train/test split: held-out RMSE (≈5.6×10⁻⁵) matches the
  training RMSE, so the model generalizes across the range rather than overfitting.

## Fitted parameters

Baseline:

| param | value |
|-------|-------|
| c | 0.07403 |
| A | 0.07420 |
| k | 0.68496 |
| B | −0.05971 |

Localized Gaussian effects `(amplitude G, center μ, width σ)`:

| # | G | μ | σ | interpretation |
|---|-----|------|------|----------------|
| 1 | 0.20027 | −1.00028 | 0.35376 | main calibration bump (σ ≈ 1/(2√2)) |
| 2 | 0.03193 | 1.75338 | 0.36930 | high-compute localized feature |
| 3 | 0.04693 | 2.28638 | 0.59103 | high-compute localized feature |
| 4 | −0.00519 | −1.20909 | 0.77997 | small broad correction |

## Fit quality (training data)

- **RMSE ≈ 5.6 × 10⁻⁵**
- **Max absolute error ≈ 3.5 × 10⁻⁴**

## Notes / uncertainty

- The main peak (component 1) and the exp+linear baseline are robust and well-determined
  across many fitting restarts and the train/test split.
- The smaller high-compute components (2–4) are the least uniquely identified part of the
  model: adding one more Gaussian drives training RMSE to ~5×10⁻⁶ but with degenerate
  parameters, indicating diminishing returns / mild non-identifiability rather than new
  structure. The reported 4-Gaussian model was chosen as the best trade-off between
  accuracy and parameter stability; since the evaluation points lie within the observed
  `logC` range, it should predict them to well within 10⁻³.
