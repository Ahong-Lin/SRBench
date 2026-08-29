# Discovered Law for `dN_dt`

## Summary

The instantaneous right-hand side is a **linear demographic model in the two
population variables with seasonally (period‑1) varying coefficients**:

$$\frac{dN}{dt} = A(t) + B(t)\,N + C(t)\,R$$

where

- `N` = total abundance,
- `R` = `reproductive_adult_abundance`,
- `A(t)`, `B(t)`, `C(t)` are periodic functions of time with **fundamental period = 1.0** (angular frequency `w = 2π`), represented as truncated Fourier series (6 harmonics each).

This reproduces the training trajectory with **R² = 0.99987 (RMSE ≈ 0.60)** and,
under a right-hand time hold-out that mimics the hidden test, extrapolates with
**R² ≈ 0.999 (RMSE ≈ 1.5)**.

## Methodology

1. **Verified the target.** A finite-difference `dN/dt` of the `N` column matches
   the `dN_dt` column to 6+ digits, confirming the target is the true state derivative.

2. **Ruled out an autonomous 2‑variable law.** `dN_dt` is *not* a single-valued
   function of `(N, R)`: many pairs of rows share nearly identical `(N, R)` (within
   0.5) yet have derivatives of opposite sign (e.g. `-20` vs `+64`). A degree‑6
   polynomial in `(N, R)` only reaches R² ≈ 0.28. A hidden oscillatory degree of
   freedom is present, so time must enter explicitly.

3. **Identified the oscillation.** Zero-crossings of `dN_dt` and a frequency scan
   both point to a period very close to 1.0. Fitting on the left 80 % of the time
   axis and predicting the right 20 % (the same extrapolation geometry as the real
   test) selected `w = 6.268 ≈ 2π`, i.e. an **exact seasonal period of 1.0**. The
   small apparent frequency drift seen with a single global sinusoid was a transient
   artifact of the growing mean, not a real change in period.

4. **Found the functional form.** With `w = 2π`, the model
   `dN/dt = A(t) + B(t)N + C(t)R` (linear in the populations, periodic coefficients)
   is both accurate and interpretable. Adding polynomial terms in `N, R` did not
   improve hold-out accuracy; keeping the model linear in the populations did.
   Six harmonics per coefficient were chosen by hold-out validation (more harmonics
   gave no further test-set gain).

## Interpretation

- **`C(t)·R`** — recruitment: reproductive adults produce offspring at a
  seasonally modulated rate. `C(t)` is strongly positive with a pronounced annual
  pulse (dominant harmonic amplitude ≈ 0.7 on a mean ≈ 0.85).
- **`B(t)·N`** — loss/self-limitation of the total stock; `B(t)` is negative on
  average (net mortality ≈ 0.85/unit time) with a modest seasonal component.
- **`A(t)`** — seasonal baseline flux.

The combination of seasonal recruitment and near-constant mortality produces the
observed oscillation of period 1 superimposed on a logistic-like approach of the
mean toward carrying capacity.

## Fitted parameters

Angular frequency `w = 2π`, `K = 6` harmonics. Each coefficient function is
`f(t) = a₀ + Σₖ [aₖˢ·sin(k·w·t) + aₖᶜ·cos(k·w·t)]`.

| term | a₀ | (k=1 sin, cos) | (k=2) | (k=3) | (k=4) | (k=5) | (k=6) |
|------|-----|----------------|-------|-------|-------|-------|-------|
| A(t) | 62.731 | 33.049, 11.325 | 7.048, −9.508 | −7.170, 0.002 | 0.282, 3.904 | 1.775, 0.421 | −0.026, −0.428 |
| B(t) | −0.8476 | −0.3093, −0.1135 | −0.1259, 0.0458 | −0.0109, −0.0118 | −0.0405, −0.0558 | −0.0399, −0.0351 | 0.0401, −0.0496 |
| C(t) | 0.8468 | 0.6900, 0.2962 | 0.2307, −0.1444 | −0.0567, 0.0146 | 0.0545, 0.1113 | 0.0696, 0.0448 | −0.0576, 0.0642 |

(The exact double-precision values are embedded in `law.py`.)

## Notes on validity / extrapolation

Because the coefficients are bounded periodic functions and the law is linear in
`N` and `R`, predictions remain stable as `t` advances beyond the training window
and as `N, R` drift to slightly larger values on the continuing trajectory. The
right-edge hold-out residuals stay small (max |error| ≈ 3.5 against a target range
of ≈ 200), supporting use on the hidden right-hand time segment.
