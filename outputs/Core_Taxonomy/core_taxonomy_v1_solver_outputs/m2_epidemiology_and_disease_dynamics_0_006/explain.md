# Dose–Response Law for Probability of Infection

## Summary

The instantaneous probability of infection as a function of ingested pathogen
dose `d` is well described by a **minimum-infectious-unit ("at least two hits")
dose–response model** with **saturating pathogen establishment**:

```
lambda(d) = a * d^p / (1 + (d/K)^h)          # expected number of established organisms
p_inf(d)  = P[N >= 2],  N ~ Poisson(lambda)
          = 1 - exp(-lambda) * (1 + lambda)
```

Fitted parameters (on the clean `p_inf` column of `train_data.csv`):

| parameter | value        | meaning                                        |
|-----------|--------------|------------------------------------------------|
| `a`       | 6.4288e-03   | low-dose establishment-rate coefficient        |
| `p`       | 0.95065      | dose exponent (essentially linear uptake)      |
| `K`       | 391.53       | saturation dose scale                          |
| `h`       | 0.88061      | saturation sharpness                           |

**Fit quality:** R² = 0.99992, RMSE = 2.1e-3, max absolute error = 4.8e-3,
max relative error = 5.4% (worst case at the smallest doses).

## Mechanistic interpretation

The data span four decades of dose (`d` = 1 … 10⁴) with `p_inf` rising from
~2×10⁻⁵ to ~0.66. Two robust qualitative features drive the model choice:

1. **Low-dose scaling `p_inf ∝ d²`.** A log–log regression over `d ≤ 1.5`
   gives a slope of 1.96 (→ 2 as `d → 0`). A probability that grows as the
   *square* of dose is the signature of a **cooperative / threshold**
   requirement: a single organism is not enough — at least **two** organisms
   must independently survive and establish for infection to occur. If `N`, the
   number of established organisms, is Poisson with mean `λ`, then at low mean
   `P[N ≥ 2] ≈ λ²/2`, giving the observed quadratic onset.

2. **Broad, sub-unity saturation.** The response does not sharply switch on; the
   local log–log slope drifts smoothly from ~2 down toward ~0.1 over four
   decades, and `p_inf` is still only ~0.66 at `d = 10⁴`. This rules out a
   sharp Hill/threshold and instead points to **saturating establishment**: the
   expected number of organisms that successfully establish, `λ(d)`, grows
   nearly linearly at low dose but rolls off at high dose because host clearance
   capacity (immune competence) is *held fixed* across the experiment. As `λ`
   saturates, `p_inf = 1 − e^{−λ}(1+λ)` approaches a plateau below 1.

Putting these together: `λ(d) = a·d^p/(1+(d/K)^h)` is the saturating expected
establishment count, and infection is the event that this Poisson count reaches
the minimum infectious unit of 2.

## Methodology

1. **Exploration.** Loaded the data and characterized the local log–log slope
   `s(d) = d·ln'(p_inf)`. It decreases monotonically from ≈2 (low dose) toward
   ≈0.1 (high dose), immediately excluding constant-exponent forms (power law,
   simple Hill) and single-hit forms (exponential, standard beta-Poisson), all
   of which have a low-dose slope of 1.

2. **Candidate screening.** Fit and compared many closed forms: exponential
   `1−e^{−d/k}`, Weibull, Hill, log-probit, (generalized) beta-Poisson
   `1−(1+(d/b)^g)^{−a}`, and scaled variants. The slope-2 low-dose behavior was
   only captured by "≥ 2 events" structures.

3. **Model identification.** Adopting `p_inf = P[N≥2]` with `N ~ Poisson(λ)`,
   the data were inverted to recover `λ(d)` empirically. `λ(d)` is a saturating
   function with a near-linear low-dose regime, which was parameterized as
   `a·d^p/(1+(d/K)^h)`.

4. **Fitting.** Parameters were estimated by nonlinear least squares on the
   *relative* residuals `(pred − p_inf)/p_inf` (so the five-orders-of-magnitude
   spread of `p_inf` is weighted sensibly). This yields the values above with
   R² = 0.99992.

## Implementation

`/app/law.py` implements the formula exactly, mapping each input row's `d` to a
single `p_inf` prediction with no state, data access, or ordering dependence.
The output is clamped to `[0, 1]`.

## Limitations

The empirically recovered `λ(d)` is not perfectly captured by the two-parameter
saturation term, leaving a residual worst-case relative error of ~5% at the very
smallest doses (where `p_inf ~ 10⁻⁵`); absolute error there is ~10⁻⁵. The
exponents `p ≈ 0.95` and `h ≈ 0.88` are close to but not exactly 1, which likely
reflects the true saturation mechanism being slightly richer than a single
saturable step. The mechanistic structure (quadratic low-dose onset + saturating
establishment) is nonetheless strongly supported by the data.
