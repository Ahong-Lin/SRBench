# Conduction velocity vs. axon diameter

## Summary

The conduction velocity `v` of a depolarization wave on an unmyelinated axon is
a **saturating, S-shaped function of diameter `d`**. It rises steeply from
essentially zero at small diameter, passes through an inflection near `d ≈ 11`,
and levels off toward an asymptotic ceiling `Vmax ≈ 3.13` at large diameter.

The relationship is captured by a **generalized-logistic (sigmoidal) law** in
which the *log-odds* of the normalized velocity is a smooth polynomial in
`ln(d)`:

```
v(d) = Vmax / (1 + exp(-P(ln d)))

P(u) = -0.007968 u^7 + 0.039776 u^6 - 0.019241 u^5 - 0.065917 u^4
       + 0.059808 u^3 - 0.309650 u^2 + 2.303961 u - 4.786505     (u = ln d)

Vmax = 3.12649
```

## Discovered structure of the curve

The data span `d ∈ [0.5, 30]`, `v ∈ [0.0045, 3.086]`. Three regimes were
identified:

1. **Small-diameter power-law rise.** For `d ≲ 2`, `v` grows roughly as a power
   law `v ∝ d^n` with a *diameter-dependent* exponent that increases toward
   `n ≈ 2.7–3` as `d → 0.5`. Larger diameter sharply lowers internal
   longitudinal resistance, so velocity climbs quickly.

2. **Transition / inflection.** The log–log slope decreases monotonically as
   diameter grows. The absolute slope `dv/dd` peaks at `d ≈ 10.9`, where
   `v ≈ 1.55 ≈ Vmax/2` — the inflection point of the sigmoid.

3. **Large-diameter saturation.** For `d ≳ 15` the velocity approaches a
   plateau. Fitting the right tail as `Vmax − A·e^{-k d}` gives a clean
   exponential approach with `Vmax ≈ 3.11`, `A ≈ 17.0`, `k ≈ 0.21`
   (relative error ~0.1%). Beyond this diameter, further increases in `d`
   barely change `v`: resistance is no longer the rate-limiting factor.

Because the effective log–log exponent falls smoothly from ~2.7 to 0 (rather
than staying at any single fixed value), no single fixed-exponent power law or
plain Hill/Weibull/Gamma form reproduces the whole curve. A logistic in `d`
captures the exponential right tail but overshoots at small `d`; a Hill function
(logistic in `ln d`) is too symmetric. The data are asymmetric — power-law on
the left, exponential saturation on the right. Expressing the log-odds
`ln(v/(Vmax−v))` as a polynomial in `ln d` accommodates this asymmetry with a
single smooth expression.

## Methodology

1. **Loaded** `train_data.csv` (4500 rows). The noise-free column `v` was used
   as the target (`v_noisy` has additive noise, σ ≈ 0.05, and was ignored).
2. **Diagnosed the shape**: confirmed `v` is smooth and monotone with a single
   inflection (one sign change in the second difference); located the
   inflection at `d ≈ 10.9`, `v ≈ Vmax/2`.
3. **Estimated the asymptote** `Vmax ≈ 3.11–3.13` from an exponential fit of the
   saturating right tail.
4. **Linearized** with the logit transform `g = ln(v/(Vmax−v))` and found that
   `g` is well described by a low-order polynomial in `ln d` (not in `d`,
   `√d`, or `1/d`), motivating the generalized-logistic form.
5. **Fit** the full model `v = Vmax/(1+exp(−P(ln d)))` by nonlinear least
   squares on `ln v` (which balances the accuracy across the four orders of
   magnitude in `v`). A degree-7 polynomial for `P` was selected as the best
   accuracy/parsimony trade-off; the fit is monotone over the whole domain.

## Fitted parameters

| Parameter | Value |
|-----------|-------|
| `Vmax`    | 3.126492946862683 |
| `P` coeffs (u^7 … u^0) | −0.00796756, 0.03977627, −0.01924077, −0.06591714, 0.05980841, −0.30964982, 2.30396080, −4.78650549 |

## Fit quality (training data)

| Metric | Value |
|--------|-------|
| R²                 | 0.99992 |
| RMS error          | 0.0099 |
| Max relative error | 0.0089 (0.89%) |
| Max |Δln v|         | 0.0089 |

## Implementation

`law.py` evaluates the closed form pointwise: for each row it computes
`u = ln(d)`, evaluates the polynomial `P(u)` by Horner's method, and returns
`Vmax / (1 + exp(−P(u)))`. It uses only the input variable `d` and the fixed
fitted constants, with no state, data access, or ordering dependence.
