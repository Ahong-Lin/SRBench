# Discovering the law for `dE_dt`

## Result

The instantaneous rate of change of the active enzyme concentration is, **exactly**:

$$
\frac{dE}{dt} \;=\; -0.01\,E^{2} \;-\; 0.1\,E \;+\; \left(0.4 - \frac{0.6}{E+2}\right) A .
$$

It is a pointwise function of the state variables `E` and `A` only. On the full
training set this reproduces the reference `dE_dt` to machine precision:

| metric | value |
|---|---|
| max abs error | ≈ 1.6 × 10⁻¹⁵ |
| RMSE | ≈ 3 × 10⁻¹⁶ |

`t` and `G` are **not** required: `G` obeys its own equation in the same reaction
network but does not feed back into the active-enzyme balance, and there is no
explicit time dependence.

## How it was found

### 1. The data are clean and `dE_dt` is a true derivative
A smoothing-spline derivative of `E(t)` matches the supplied `dE_dt` column to
~2 × 10⁻⁷, so the dataset is essentially noiseless and `dE_dt = d/dt E`. This
justified hunting for an exact closed form rather than a statistical fit.

### 2. A naive first-order decay fails
At `t = 0`: `E = 10, A = 0, dE_dt = -2`, suggesting a rate `0.2·E`. But `E`
actually rises above its initial value and `dE_dt` turns positive later, so the
active pool is regenerated — a simple `-kE` decay is wrong. A best linear fit
`dE_dt = aE + bA` leaves a max error of 0.32, and polynomials in `(E,A,G)`
plateaued around 0.01 — a tell-tale sign of a hidden **non-polynomial** term.

### 3. Reconstruct the reaction network from exact sub-relations
Using clean spline derivatives of the other columns, two relations came out
*exactly* (max error ≈ 1e-6, limited only by the numerical derivative):

* **Aggregate dynamics** — an autocatalytic (Finke–Watzky-like) law:
  $$\dot G = 0.02\,A + 0.05\,A\,G - 0.05\,G.$$
* **Total source** — summing the three derivatives:
  $$\dot E + \dot A + \dot G = 0.2\,E - 0.01\,E^{2} - 0.05\,G.$$

Subtracting gives an exact polynomial for the native+unfolded pool,
`Ė + Ȧ = 0.2E - 0.01E² - 0.02A - 0.05AG`, which pins down the production term
(logistic synthesis `0.2E - 0.01E²`) and the loss of `A` to aggregation
(`-0.02A - 0.05AG`).

### 4. Isolate the folding/unfolding exchange
Everything left in `dE_dt` after removing the production/unfolding E-terms is
the **refolding flux** `R = dE_dt + 0.1E + 0.01E²`. Empirically `R = kr(E)·A`
with `R = 0` when `A = 0`, and `kr = R/A` proved to be a clean function of `E`
alone (independent of `A` and `G`). Testing candidate forms, a rational form
fit it perfectly:

$$
k_r(E) = 0.4 - \frac{0.6}{E+2}.
$$

Substituting back and confirming with a nonlinear least-squares fit recovered
the constants exactly as `{0.4, 0.6, 2, 0.1, 0.01}` with residual ~1e-15.

## Mechanistic interpretation

The system is a thermal-inactivation network `N ⇌ U → aggregate` with enzyme
turnover:

* `E` = native/active enzyme `N`, `A` = reversibly unfolded intermediate `U`,
  `G` = aggregate.
* **Production / regeneration** of native enzyme is logistic: `+0.2E − 0.01E²`.
* **Unfolding** `N → U` is first order: `−0.3E`.
* **Refolding** `U → N` occurs with a concentration-dependent rate constant
  `kr(E) = 0.4 − 0.6/(E+2)` that saturates toward `0.4` when native enzyme is
  abundant and is suppressed when `E` is low — a cooperative/templated
  refolding effect.

Grouping the `E`-only pieces (`0.2E − 0.01E² − 0.3E`) yields the compact form
`−0.1E − 0.01E² + kr(E)·A` implemented in `law.py`.

## Why this extrapolates to the held-out (later-time) segment

The test set is the right-hand time segment, where `E` continues to fall, `A`
declines and `G` grows. Because the law is the **true mechanistic right-hand
side** (a function of `E` and `A` only, with the aggregate `G` correctly shown
to be irrelevant to `dE/dt`), it is not a curve-fit that degrades outside the
training window — it holds pointwise wherever `E` and `A` take physical values,
including the lower-`E` region reached at later times.

## Implementation notes

`law(input_data)` maps each row independently, reads only `E` and `A`, uses
fixed constants, and returns a list with a single `{"dE_dt": ...}` dict — no
state, ordering, interpolation, or data access.
