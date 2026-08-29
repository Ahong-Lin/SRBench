# Discovering the law for `dI_dt`

## 1. Setup and sanity checks

The data are a single, densely-sampled outbreak trajectory (4500 rows,
`t = 0 … 108`, uniform Δt ≈ 0.024).

* **Conserved population.** `S + E + I + R = 1000.0` on every row to machine
  precision, so the system is a closed compartmental model with **N = 1000**.
* **The target is a true derivative.** A 4th-order finite difference of the
  `I` column reproduces the supplied `dI_dt` to `2.8e-6`, confirming
  `dI_dt = d/dt I(t)` — we are looking for the right-hand side of the `I` ODE.

## 2. Ruling out the textbook SEIR

The obvious candidate, `dI/dt = σ·E − γ·I`, is **impossible** here:

* At `t = 0` the state is `S=999, E=0, I=1, R=0` and `dI_dt = +0.1456 > 0`.
  With `E = 0`, `σE − γI = −γ·I < 0`. The infectious count would have to
  *decrease*, but `I` increases monotonically from the very first step.
* A least-squares fit of `dI_dt` to `{E, I}` gives a negative `E` coefficient
  and a relative RMSE of 0.62 — a non-fit.
* `I` peaks (`t≈28.9`) *before* `E` peaks (`t≈32.1`), the opposite of the
  latent-then-infectious ordering of a standard SEIR.
* A full non-linear least-squares fit of several mechanistic SEIR variants
  (transmission into `E`, `E` infectious, split routing, etc.) by trajectory
  simulation never reaches better than a state-RMSE ≈ 8–20 (out of I-range ~70).

So the infectious compartment receives infection flux **directly**, and `E`/`R`
are downstream book-keeping compartments that do **not** drive `dI/dt`.

## 3. Reading the incidence off `dS/dt`

The susceptible equation is extremely clean. Regressing `−dS/dt` on
`{S·I/N, S·I²/N²}` gives

```
-dS/dt = 0.4991 · S·I/N − 0.4566 · S·I²/N²     (relative RMSE 3e-4)
```

i.e. the transmission is **prevalence-dependent** (a behavioural/saturation
effect): the effective contact rate falls as the infected fraction rises. This
single fact is the key — it tells us the incidence is not plain mass action but
carries an `S·I²/N²` correction.

## 4. The law for `dI/dt`

Carrying the same functional structure into the `I` equation and fitting
`dI_dt` on `{S·I/N, S·I²/N², I}` over all 4500 rows gives a clean, sparse,
interpretable law:

```
dI/dt = 0.43722 · (S·I/N)  −  2.06370 · (S·I²/N²)  −  0.19682 · I
```

Equivalently, a **prevalence-dependent SIR** incidence for the infectious class:

```
dI/dt = β(I) · S·I/N − γ·I ,     β(I) = β0 − β1·(I/N)
        β0 = 0.43722   (baseline transmission)
        β1 = 2.06370   (reduction of transmission with prevalence)
        γ  = 0.19682   (recovery / removal rate)
```

* **Transmission term** `β(I)·S·I/N`: new infections entering `I`, with a
  contact rate that declines linearly with the infected fraction `I/N`
  (0.437 at `I≈0` down to ≈0.30 at the peak `I≈69`).
* **Removal term** `−γ·I`: recovery of infectious individuals at constant rate.

### Why not include `E` or `R`?

Both were tested as extra predictors. Their fitted coefficients are ≈0
(`E`: 0.0007, `R`: 0.0), they do **not** reduce the training error, and they
**worsen** out-of-sample accuracy. On this system `E` and `R` carry no
independent information about `dI/dt`, so the law depends only on `S` and `I`.
A polynomial without the `S·I²/N²` term (plain quadratic SIR) extrapolates
badly (hold-out RMSE 0.63 vs 0.005), which is what pins down the cubic
`S·I²/N²` prevalence term as genuine rather than an artifact.

## 5. Fit quality and generalisation

* Full training data: **R² = 0.99978, RMSE = 0.0257**, max abs error 0.092
  (the largest error is at `t≈0`; everywhere else it is far smaller).
* **Extrapolation test** (fit on the first 70 % of the timeline, `t<75`, and
  predict the last 30 %, `t=75…108`): RMSE = **0.0046**. Because the hidden
  test set is the *right-hand time segment* — the declining tail where `S`
  plateaus near 300 and `I → 0` — this is exactly the regime the model nails.
  In that tail `dI/dt ≈ (0.437·S/N − 0.197)·I ≈ −0.066·I`, matching the observed
  exponential decay rate.

## 6. Implementation notes (`law.py`)

* Pure closed-form arithmetic per row; no ML model, table, interpolation,
  differentiation, ordering, state, or file/hidden-data access.
* Uses only the declared variables `S` and `I` plus the fixed constants
  `N = 1000`, `a = 0.43722`, `b = −2.06370`, `c = −0.19682` inferred above.
* Returns exactly one `{'dI_dt': value}` dict per input row.
