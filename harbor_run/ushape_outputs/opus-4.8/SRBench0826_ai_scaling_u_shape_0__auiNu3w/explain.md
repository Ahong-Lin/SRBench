# Discovered law for `Brier` vs `logC`

## Summary

The data is a smooth, essentially **noise-free** analytic curve (a local
cubic fit leaves residuals of ~1e-9, i.e. the samples lie on an exact
function). The relationship is **non-monotonic**: an overall U‑shaped scaling
trend (Brier high at both extremes of compute, minimum near `logC ≈ 0.25`) with
one **prominent localized bump** sitting on top of it near `logC ≈ -1`.

The recovered closed form is a **smooth baseline + a sum of localized Gaussian
"bumps"**:

```
Brier(x) = c0 + c1·x + c2·x² + c3·x³  +  Σ_k  A_k · exp( -(x - μ_k)² / (2·s_k²) )
```

where `x = logC`.

## Structure of the curve

Finite-difference analysis of the extrema (Savitzky–Golay derivative) shows:

| feature | logC | Brier |
|---|---|---|
| left local minimum | -1.92 | 0.212 |
| local **maximum** (main bump) | -1.02 | 0.367 |
| global minimum | +0.26 | 0.147 |
| rises monotonically thereafter | +3.0 | 0.496 |

So there is a broad valley (poorest scores at very low and very high compute,
best around `logC ≈ 0.25`) with a distinct **localized hump centred at
`logC ≈ -1.0`** — a region where added compute *transiently hurts* the Brier
score before improving again.

## Fitting method

1. Confirmed the data is noise-free (local polynomial residual std ≈ 7e-10).
2. Modeled a smooth polynomial baseline plus Gaussian bumps (localized effects,
   as hinted). Pure quadratic + one bump left structured residuals; a cubic
   baseline plus several Gaussians removes them.
3. Fitted all parameters simultaneously with `scipy.optimize.curve_fit`
   (Levenberg–Marquardt).
4. **Model selection by cross-validation** (random 2/3 train, 1/3 held-out).
   Validation error kept dropping as bumps were added and then leveled off;
   the chosen cubic-baseline + 5-Gaussian model gives held-out
   `max error ≈ 5e-4`, confirming it generalizes across the range (the hidden
   evaluation points are interpolations within the observed `logC ∈ [-3, 3]`).

## Fitted parameters

Baseline `c0 + c1·x + c2·x² + c3·x³`:

| c0 | c1 | c2 | c3 |
|---|---|---|---|
| 0.1234196 | -0.002267291 | 0.02830533 | 0.004564549 |

Gaussian bumps `A·exp(-(x-μ)²/(2s²))`:

| # | A | μ | s | interpretation |
|---|---|---|---|---|
| 1 |  0.1688701  | -1.015833  | 0.3394543 | main localized hump near logC≈-1 |
| 2 |  0.06220959 | -0.5900829 | 0.6440599 | broadens/shapes the hump's right flank |
| 3 |  0.006146539|  0.6979127 | 0.2684551 | small correction near the valley floor |
| 4 | -0.02314605 | -0.2891183 | 0.3357512 | small dip between hump and valley |
| 5 |  0.04830997 |  1.840273  | 0.4638322 | secondary bump on the high-compute rise |

(Gaussians 1 and 2 together form the single visible hump at `logC ≈ -1`; the
others are small shape corrections.)

## Accuracy

On the full training set the closed form achieves:

- RMSE ≈ **2.1e-4**
- max absolute error ≈ **5.3e-4**

Cross-validated held-out error is of the same order (max ≈ 5e-4), so the law
generalizes across the observed `logC` range rather than overfitting.

## Implementation

`/app/law.py` evaluates the formula above with the fitted constants hardcoded
(no dependence on the training file at runtime) and returns one
`{"Brier": value}` per input row.
