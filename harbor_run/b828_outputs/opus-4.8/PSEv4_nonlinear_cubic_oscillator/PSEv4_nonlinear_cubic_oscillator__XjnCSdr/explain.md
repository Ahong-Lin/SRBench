# Discovered law for `dv_dt`

## Result

The data are governed by a **damped cubic (Duffing-type) oscillator with an
amplitude-dependent damping coefficient**:

$$
\frac{dv}{dt} = -a\,x^{3} \;-\; \bigl(b - m\,|x| - n\,x^{2}\bigr)\,v
$$

with parameters fitted from `train_data.csv`:

| param | value | role |
|-------|-------|------|
| `a` | 2.25049505 | cubic restoring stiffness (≈ 9/4) |
| `b` | 0.69869719 | damping coefficient at `x = 0` |
| `m` | 0.18463584 | linear reduction of damping with `|x|` |
| `n` | 0.03992012 | quadratic reduction of damping with `x²` |

The right-hand side is **autonomous** — it depends only on `x` and `v`; the
time `t` does not enter (its coefficient fits to ~0), consistent with an
unforced oscillator relaxing from `x=1.2, v=0`.

## How it was found

The data is a single decaying-oscillation trajectory (`t = 0 … 36`).

1. **Restoring force (turning points, `v ≈ 0`).** At the velocity zero-crossings
   the acceleration is purely the restoring term. The ratio `dv_dt / x³` equals
   **−2.25 exactly** at both large-amplitude turning points (`x=1.200 → −3.888`
   and `x=−0.7035 → +0.785`), while `dv_dt / x` was not constant. This pins the
   restoring force to a pure cubic `−2.25 x³` (no linear `x` term — its fitted
   coefficient is ~2×10⁻⁴).

2. **Damping (near `x ≈ 0`).** With the restoring term removed, `dv_dt + 2.25 x³`
   is the damping term. On the `x ≈ 0` slice (spanning `v` from −0.93 to +0.16)
   the ratio `(dv_dt+2.25x³)/v` is constant at **−0.699**, so the damping is
   **linear in `v`** (no quadratic/`v|v|` drag) with coefficient `b ≈ 0.699` at
   the origin.

3. **Amplitude dependence of damping.** Binning the effective damping
   coefficient `c(x) = -(dv_dt+2.25x³)/v` versus `|x|` shows it is **symmetric in
   `x`** (identical for `x>0` and `x<0`) and decreases almost linearly from
   `0.70` at `x=0` to `0.56` at `|x|=0.68`. A pure `x²` law fails badly; a linear
   `|x|` law fits well, and a small additional `x²` correction closes the
   remaining gap. Hence `c(x) = b - m|x| - n x²`.

## Fit quality

Fitting all four parameters on the full training set:

- R² = 0.9999999
- RMSE = 1.2 × 10⁻⁴
- max abs error = 1.2 × 10⁻³

This is at the level of the reference solver's own integration truncation error.
Adding further terms (`x`, `v³`, `x²v`, `t`, …) yields coefficients ≈ 0 and no
meaningful improvement, and a random 3000/1500 train/test split confirms the
model generalizes (test RMSE ≈ 1.3 × 10⁻⁴).

## Implementation

`law.py` implements the relation pointwise:

```python
dv_dt = -A * x**3 - (B - M*abs(x) - N*x**2) * v
```

evaluating each input row independently using only `x` and `v`.
