# Discovered Law for `dv_dt`

## Formula

```
dv_dt = A1·x + A3·x³ + B1·v + B3·v³ + C·Fh + D·Fh2
```

with fitted parameters:

| term | coefficient |
|------|-------------|
| `x`    | A1 = -0.997630 |
| `x³`   | A3 = -0.053287 |
| `v`    | B1 = -0.027547 |
| `v³`   | B3 = -0.013426 |
| `Fh`   | C  = -0.103122 |
| `Fh2`  | D  = -0.051050 |

The intercept is ~1×10⁻⁴ and was dropped (physically, dv_dt = 0 at rest with no forcing).

## Interpretation

This is a **Duffing-type nonlinear oscillator**:

- `A1·x` ≈ `-x` is the dominant linear restoring force (natural frequency ≈ 1).
- `A3·x³` is a small **hardening** cubic stiffness correction (negative sign, adding to the restoring force as amplitude grows).
- `B1·v + B3·v³` is weak **nonlinear damping** (linear plus cubic in velocity).
- `C·Fh + D·Fh2` are two **external forcing channels** supplied as inputs; they are used pointwise as given.

The oscillation amplitude slowly grows over the observed window (|x| rising from 1.0 toward ~1.17), consistent with the mild forcing driving the system.

## Methodology

1. **Baseline linear fit** on `{x, v, Fh, Fh2, 1}` gave residual std ≈ 0.013 — good but structured.
2. **Residual correlation analysis** revealed the residual correlated with `x³` (r ≈ −0.32); adding `x³` dropped std to ≈ 0.0035.
3. The new residual correlated with `v³` (r ≈ −0.31); adding it dropped std to ≈ 0.0006.
4. Further candidate terms (`x²v`, `x·Fh`, `x·v²`, `x⁵`, `t`, …) gave only marginal gains and were rejected to avoid overfitting the extrapolation segment.
5. All coefficients obtained by ordinary least squares (`numpy.linalg.lstsq`).

## Validation

- **Full-data residual**: std = 6.2×10⁻⁴, max abs error = 1.5×10⁻³, MSE ≈ 3.9×10⁻⁷ (target std ≈ 0.84).
- **Extrapolation test**: fitting on the first 75% of the time series and predicting the final 25% (mimicking the hidden right-hand segment) gave residual std ≈ 8×10⁻⁴ and max abs error ≈ 2×10⁻³, with coefficients stable versus the full fit. This confirms the law generalizes beyond the observed time window.

## Notes on constraints

The `law` function maps each row independently using only `x, v, Fh, Fh2` and the fixed fitted constants above — no state, ordering, differentiation, lookup, or data access.
