# Discovered Law: Brier vs. log-Compute

## Summary

The relationship between training compute (`logC`, denoted `x` below) and the
held-out `Brier` score is **non-monotonic**. Visual inspection and residual
analysis reveal three superimposed components:

1. A **smooth global trend** (a shallow, slightly asymmetric bowl that rises on
   both ends of the range).
2. A **localized bump** centered near `logC ≈ -1.0`, where the Brier score
   temporarily worsens (an "inverse-scaling" pocket) before recovering.
3. A **smooth oscillatory structure** riding on top of the trend, well described
   by a few low-frequency sinusoids.

The recovered closed form is:

```
Brier(x) = a + b·x + c·x² + d·x³                 (cubic trend)
         + A·exp(-(x - μ)² / (2·σ²))             (localized Gaussian bump)
         + e₁·sin(w₁·x + p₁)
         + e₂·sin(w₂·x + p₂)                     (oscillatory structure)
         + e₃·sin(w₃·x + p₃)
```

with `x = logC`.

## Fitted parameters

Fit by non-linear least squares (`scipy.optimize.curve_fit`) on the full
training grid.

| Component | Parameter | Value |
|-----------|-----------|-------|
| Cubic trend | a | 0.135655 |
|             | b | 0.016446 |
|             | c | 0.028210 |
|             | d | 0.002428 |
| Gaussian bump | A (amplitude) | 0.236739 |
|               | μ (center)    | -1.010428 |
|               | σ (width)     | 0.359514 |
| Sinusoid 1 | e₁, w₁, p₁ |  0.012957, 3.183665, 1.870824 |
| Sinusoid 2 | e₂, w₂, p₂ | -0.002766, 5.463609, 1.146127 |
| Sinusoid 3 | e₃, w₃, p₃ |  0.000255, 7.880259, 1.240511 |

## Interpretation

- The **Gaussian bump** at `μ ≈ -1.0` (amplitude ≈ 0.24, width σ ≈ 0.36) is the
  dominant "localized effect": it lifts the Brier score to a local maximum
  (~0.37) around `logC = -1`, flanked by dips near `logC ≈ -1.9` and the global
  minimum (~0.147) near `logC ≈ +0.2`.
- The **cubic trend** captures the broad, asymmetric baseline: Brier climbs
  faster on the high-compute (right) side than on the low-compute (left) side.
- The **sinusoids** capture a genuine, smooth wave in the data whose amplitude
  is small (dominant term e₁ ≈ 0.013) but systematic. The first sinusoid
  (period ≈ 2 in `logC`) accounts for most of it; the higher-frequency terms are
  progressively smaller refinements.

## Fitting method & validation

- **Method:** Levenberg–Marquardt least squares (`curve_fit`). Starting values
  were obtained by (i) fitting a quadratic/cubic + single Gaussian to expose the
  main bump, then (ii) analyzing the residual — which showed a clean, smooth
  oscillation — and adding sinusoidal terms until the residual reached the noise
  floor.
- **Data character:** The training set is 4500 points on a near-uniform grid
  (spacing ≈ 0.0012) over `logC ∈ [-3, 3]`, and is effectively noiseless.
- **Accuracy on training data:** RMSE ≈ **2.1 × 10⁻⁴**, max abs error ≈
  **1.2 × 10⁻³** (worst at the extreme endpoints). Relative to the output
  standard deviation (≈ 0.086) this is R² ≈ 0.99999.
- **Generalization:** An 80/20 random hold-out gives test RMSE ≈ train RMSE
  (≈ 2.5–2.7 × 10⁻⁴ for the 2–3 sinusoid models), confirming no overfitting.
  Adding further sinusoids only produced degenerate/near-canceling terms, so the
  model was capped at three, keeping the form compact and interpretable.

## Implementation

`law.py` evaluates the closed form directly (vectorized with NumPy) and returns
one `{"Brier": value}` per input row.
