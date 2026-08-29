# Discovered Law for `dv_dt`

## Result

The data are governed by a **nonlinear damped oscillator** with a purely
**cubic restoring force** and a **position-dependent linear damping** term:

```
dv_dt = a · x³ + (b + c · |x|) · v
```

with fitted constants

| parameter | value | role |
|-----------|-------|------|
| `a` | −2.25470818 | cubic restoring stiffness |
| `b` | −0.70501374 | base linear damping coefficient |
| `c` | +0.22267414 | how damping weakens with displacement (in `|x|`) |

The input `t` does **not** appear: `dv_dt` is an autonomous function of the
state `(x, v)` only.

## How it was found

1. **Linear model insufficient.** Fitting `dv_dt = αx + βv + γ` gave only
   R² ≈ 0.55, so the relationship is nonlinear.

2. **Restoring force is cubic.** Isolating rows where `v ≈ 0` (so the
   damping term vanishes) leaves `dv_dt` as a function of `x` alone. At the
   large-amplitude point `x = 1.2, v = 0` the value is exactly `−3.888 =
   −2.25 · 1.2³`, and `dv_dt / x³` is flat near `−2.25` across amplitudes.
   Hence the restoring term is `a·x³` with `a ≈ −2.25`. No linear-in-`x`
   term is needed (its fitted coefficient is ~0).

3. **Damping is linear in `v` but depends on `|x|`.** Subtracting `−2.25 x³`
   and looking at rows with `x ≈ 0` gives a clean ratio
   `(dv_dt + 2.25 x³)/v ≈ −0.70`, independent of `v` → linear damping.
   Binning that effective damping coefficient against `x` shows it is
   **symmetric in `x`** and rises (toward zero) as `|x|` grows:
   `−0.70` at `x = 0` up to `−0.42` at `x = 1.16`. A `b + c·|x|` form fits
   this far better than `b + c·x²` (maxerr 0.008 vs 0.034).

4. **Joint least-squares fit** of `{x³, v, |x|·v}` yields the parameters
   above.

## Fit quality (training data, 4500 rows)

- R² = 0.9999956
- RMSE = 7.5 × 10⁻⁴
- max abs error = 8.1 × 10⁻³

The residuals are at the level of numerical/integration noise, indicating
the functional form is essentially the true generating law.

## Implementation

`law.py` applies `dv_dt = a·x³ + (b + c·|x|)·v` to each row independently,
using only the declared variables `x` and `v` and the fixed constants above.
