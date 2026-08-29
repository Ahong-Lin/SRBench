# Discovered law: Brier score vs. log-compute

## Summary

Let `x = logC`. The Brier score is well described by a smooth polynomial
scaling trend, a small two-tone periodic ripple, and a single localized
Gaussian bump:

```
Brier(x) = a3·x³ + a2·x² + a1·x + a0          # smooth scaling trend
         + A1·sin(w1·x + p1) + A2·sin(w2·x + p2)   # periodic ripple
         + Ag·exp(-(x - μ)² / (2σ²))          # localized bump
```

## Fitted parameters

| term | parameter | value |
|------|-----------|-------|
| cubic trend | a3 | 0.00239481 |
|             | a2 | 0.02827727 |
|             | a1 | 0.01657230 |
|             | a0 | 0.13544945 |
| ripple #1 | A1 | 0.01298341 |
|           | w1 | 3.19871937 |
|           | p1 | 1.84323209 |
| ripple #2 | A2 | -0.00266075 |
|           | w2 | 5.50779119 |
|           | p2 | 1.09103988 |
| Gaussian bump | Ag | 0.23706361 |
|               | μ  | -1.00843334 |
|               | σ  | 0.35949227 |

## Structure of the relationship

The data span `logC ∈ [-3, 3]`. Three distinct features are present:

1. **Smooth scaling trend** — an almost-parabolic curve with its minimum
   near `x ≈ -0.3`, rising more steeply toward high compute (right) than low
   compute (left). A cubic captures this mild asymmetry; the dominant term is
   the `a2·x²` curvature (Brier ≈ 0.135 at the minimum, rising to ≈ 0.47 at
   `x = 3`).

2. **Localized Gaussian bump** — a pronounced, well-isolated hump centered at
   `logC ≈ -1.01` with width `σ ≈ 0.36` and height `≈ 0.237`. This is the
   "localized effect" mentioned in the experimental context: over a narrow
   compute band the Brier score jumps to a local maximum (≈ 0.366) before
   dropping again — a non-monotonic, transient degradation in calibration.

3. **Periodic ripple** — a low-amplitude oscillation (peak-to-peak ≈ 0.02)
   present across the whole range. A single sinusoid (w ≈ 3.2) removes most of
   it; a second, smaller harmonic (w ≈ 5.5, amplitude ≈ 0.0027) captures the
   remainder. Adding a third sinusoid yields negligible improvement, confirming
   two tones suffice.

## Fitting method

* Loaded the 4500-row training set with `pandas.read_csv`.
* Identified the components incrementally: the bump-free right region
  (`x > 0.2`) was fit first with `quadratic + sine`, which reduced RMSE ~15×
  and revealed the genuine periodic ripple. The far-left tail exposed the
  asymmetry (cubic term), and the residual over the full range isolated the
  clean Gaussian bump at `x ≈ -1`.
* Final parameters obtained by full non-linear least squares
  (`scipy.optimize.curve_fit`) over all 4500 points, with a 40-start random
  multistart to avoid local minima in the sinusoid frequencies.

## Fit quality

* **RMSE ≈ 2.66 × 10⁻⁴** over the training set.
* **Max absolute error ≈ 1.36 × 10⁻³**.

Residuals are smooth and structureless at this level, indicating the closed
form captures essentially all of the deterministic signal. Because the hidden
evaluation points lie within the observed `logC` range, this interpolating
form is expected to generalize well.

## Implementation

`/app/law.py` evaluates the formula above per row (pure function of `logC`,
fixed constants only — no data access, state, or ordering dependence).
