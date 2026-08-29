# Thermal inactivation of an enzyme — discovered law for `dE_dt`

## Result

```
dE/dt = -k1·E − k2·E² + kr·A
```

with constants inferred from the training data:

| constant | value | meaning |
|----------|-------|---------|
| `k1` | 0.11910 | first-order thermal unfolding / inactivation of native enzyme |
| `k2` | 0.00787 | second-order (bimolecular) aggregation of native enzyme |
| `kr` | 0.34569 | refolding of the reversibly-unfolded pool `A` back to active enzyme |

Only `E` and `A` enter the instantaneous rate of change of active enzyme; `G`
(accumulated aggregate) and `t` do not appear. Fit quality on the full training
set: **R² = 0.99990, RMSE = 0.0039, max abs error = 0.022**. On the last 20 % of
the experiment (a proxy for the held-out right-hand test segment) the RMSE is
**0.0022** — i.e. under 1 % of the local |dE/dt|.

## Biological picture

Active enzyme `E` is the folded, catalytically competent protein. On incubation
at elevated (fixed) temperature it is lost through two native-state processes and
partly replenished by refolding:

1. **First-order unfolding / inactivation** `−k1·E`. Ordinary thermal denaturation
   of a single molecule; rate proportional to how much folded enzyme remains.
2. **Second-order native aggregation** `−k2·E²`. Two folded (or partially
   destabilised) molecules collide and coalesce; the collision rate scales with
   `E²`. This is the term that makes early decay faster than a pure exponential.
3. **Refolding** `+kr·A`. `A` is the reversibly-unfolded intermediate pool. It can
   fold back to the active state, feeding enzyme *back* into `E`; this is why the
   active-enzyme trace first dips, then rebounds and overshoots near `t ≈ 10`
   before declining again as the unfolded pool is progressively drained into
   irreversible aggregate `G`.

The companion aggregate variable obeys, exactly (fit R² = 1, RMSE ≈ 1e-7),

```
dG/dt = 0.02·A + 0.05·A·G − 0.05·G
```

a Finke–Watzky-type nucleation (`0.02·A`) plus autocatalytic growth (`0.05·A·G`)
with a slow loss term — consistent with `A` being the monomeric feedstock for
aggregation. `G` itself exerts no *direct* first-order effect on the active-enzyme
balance, which is why it is absent from `dE/dt`.

## How the law was discovered

1. **Loaded and profiled** `/app/data/train_data.csv` (4500 rows, dense uniform
   time grid, single smooth trajectory). Verified that the supplied `dE_dt`
   column equals the numerical time-derivative of `E`, confirming it is the true
   right-hand side of an autonomous ODE.
2. **Sparse regression** of `dE_dt` against a polynomial library in `E, A, G`.
   The combination `{E, E², A}` dominated every search: it reaches R² = 0.99990,
   and no additional quadratic/cubic or `G`-dependent term improves *out-of-sample
   (right-segment) prediction* — extra terms lowered the training residual but
   hurt extrapolation, the signature of over-fitting a small hidden-state effect.
3. **Boundary check.** At the initial condition `E = 10, A = 0`, the law gives
   `−k1·10 − k2·100 = −1.19 − 0.79 = −1.98`, matching the measured `dE/dt(0) = −2.0`.
   The `E²` term is required to reproduce this: pure first-order decay cannot.
4. **Extrapolation validation.** Fitting on the left 60–80 % of the time series
   and predicting the right-hand segment gave RMSE 0.002–0.008; the parsimonious
   three-term model generalised markedly better than denser polynomial fits.

## Constraints honoured

- `law` maps each row independently, uses only the declared variables
  (`E`, `A` — `t`, `G` unused) and fixed constants.
- No ML black box, lookup table, interpolation, numerical differentiation,
  file reads, hidden-data access, input-ordering dependence, or cross-call state.
- Returns exactly one `{'dE_dt': ...}` dict per call.
