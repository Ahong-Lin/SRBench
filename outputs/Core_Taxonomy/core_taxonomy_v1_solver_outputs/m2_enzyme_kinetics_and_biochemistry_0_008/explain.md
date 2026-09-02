# Association rate vs. viscosity — discovered law

## Result

The effective bimolecular association rate `kon` depends on solution viscosity
`eta` through a **sum of two power laws**:

$$
k_{\mathrm{on}}(\eta) = A\,\eta^{-p} + B\,\eta^{-q}
$$

with fitted parameters

| parameter | value    | interpretation |
|-----------|----------|----------------|
| `A`       | 0.642274 | amplitude of the dominant (steep) power term |
| `p`       | 0.574189 | dominant scaling exponent (controls fall-off near reference viscosity) |
| `B`       | 0.079652 | amplitude of the shallow power term |
| `q`       | 0.140988 | weak scaling exponent (controls the slow high-viscosity tail) |

## Methodology

1. **Data.** `train_data.csv` contains 4500 rows with `eta ∈ [1, 100]`
   (log-spaced) and the clean target `kon` (plus a `kon_noisy` column whose
   residual std ≈ 0.005 indicates the measurement noise floor). The model was
   fit to the clean `kon`.

2. **Power-scaling check.** A log–log plot of `kon` vs `eta` is nearly linear,
   confirming power-scaling. A single pure power law `kon = A·eta^(-p)` captures
   the trend but leaves a systematic ~13% error, because the *local* log–log
   slope is **not constant**: it is exactly ≈ −0.50 at `eta = 1` and flattens
   monotonically to ≈ −0.37 at `eta = 100`. A pure power (fixed slope) or a
   power-plus-constant (`A·eta^-p + C`, which flattens to slope 0 at high `eta`,
   over-shooting the observed −0.37) both fail to reproduce this drift.

3. **Form selection.** A slope that is steep at small `eta` and shallow at large
   `eta` is exactly what a *sum of two power laws* produces: the steeper term
   (`eta^-p`) dominates at low viscosity, the shallower term (`eta^-q`) dominates
   at high viscosity. Fitting this form by nonlinear least squares recovers the
   parameters above. A systematic search over alternative closed forms
   (power + constant, saturating/rational `A/(1+B·eta^r)+C`, Collins–Kimball
   `1/(A+B·eta^r)`, `(a+b·eta^r)^-p`, `eta^-p·(1+eta)^q`, half-/integer-power
   bases) confirmed the two-power law as the best interpretable fit.

## Fit quality

- Coefficient of determination: **R² = 0.99999**
- Mean relative error: **0.12%**
- Median relative error: **0.13%**
- Max relative error: **0.36%** (at the endpoint `eta = 1`, at the level of the
  measurement noise)

## Physical reading

Both terms decay with viscosity, consistent with a diffusion-limited encounter
that slows as the medium thickens. The dominant near-square-root exponent
(`p ≈ 0.57`) reflects a fractional (sub-Stokesian) viscosity dependence of the
encounter rate, while the weak term (`q ≈ 0.14`) represents a slowly-decaying
contribution that keeps the rate from flattening at high viscosity. The net
effect is a smoothly varying effective power-scaling exponent that runs from
≈ 0.5 to ≈ 0.37 across the measured viscosity sweep.
