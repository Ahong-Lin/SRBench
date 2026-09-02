# Overdominance equilibrium frequency — discovered law

## Target

Predict `p_eq`, the equilibrium allele frequency at a locus maintained by
balancing selection (heterozygote advantage), from the two homozygote
selection coefficients `s1`, `s2`. Both inputs lie in ≈ `[0.005, 0.1]`.

## Key empirical finding

The textbook deterministic result for overdominance,

```
p_eq_textbook = s2 / (s1 + s2)          # frequency of allele 1
```

does **not** fit the data. Evidence:

- `corr(s2/(s1+s2), p_eq) ≈ 0.77` (a genuine law would give ≈ 1).
- The textbook value spans `(0, 1)`, but the observed `p_eq` is compressed into
  `[0.149, 0.365]` and is always below 0.5. E.g. for `s1=0.020, s2=0.086` the
  textbook value is 0.81 while the observed `p_eq` is 0.335.

So `p_eq` depends not only on the *ratio* of the coefficients but also on the
overall *magnitude* of selection.

## Natural coordinates

Two composite variables make the data collapse onto a smooth surface:

```
x = s2 / (s1 + s2)      # the classic overdominance equilibrium ratio (in [0,1])
u = sqrt(s1 + s2)       # square-root of the total selection intensity
```

Diagnostics that motivate them:

- Holding `x` fixed, `p_eq` grows with the total selection `S = s1+s2` as a
  near power-law whose exponent drifts with `x` — i.e. magnitude matters and it
  couples to the ratio.
- A polynomial in `(x, u)` reaches R² ≈ 0.9999 at **degree 4**, whereas the same
  degree in the raw `(s1, s2)` only reaches ≈ 0.999 with far larger edge error.
  `u = sqrt(S)` (not `S` itself) is what linearises the magnitude dependence,
  which is the fingerprint of a drift/selection-intensity scale.

Interpretation: `x` locates the deterministic interior equilibrium, and `u`
(the square-root of total selection intensity) carries a systematic correction
that pulls the realised equilibrium away from the naive ratio and toward the
observed `[0.15, 0.37]` band.

## Model

`p_eq` is represented as an explicit bivariate polynomial in these coordinates:

```
p_eq(s1, s2) = Σ_k  C_k · x**i_k · u**j_k ,   with  i_k + j_k ≤ 7
             x = s2/(s1+s2),   u = sqrt(s1+s2)
```

- Degree 7 → 36 fixed coefficients, obtained by ordinary least squares on
  `train_data.csv`. The full coefficient list is embedded in `law.py`
  (`_TERMS`, `_COEF`).
- Each prediction is a pure pointwise function of that single row's `s1, s2`
  (no data access, no interpolation, no state).

Simpler closed forms were tested and rejected: pure power laws
`C·s2^a·s1^b` and `C·s2^a·(s1+s2)^b` plateau at R² ≈ 0.96; `sqrt(a·s2+b·s1+c)`
and rational forms plateau at R² ≈ 0.987. The `(x, u)` polynomial is the most
accurate compact expression found.

## Fit quality

Evaluated by calling `law` once per row on the full training set
(one row per call, as the verifier does):

| metric | value |
|---|---|
| R² | 0.9999992 |
| mean relative error | 0.011% |
| max relative error | 0.13% |
| RMSE | 4.3 × 10⁻⁵ |

Cross-validation (80/20 split) gives test R² ≈ 0.9999991 and test max relative
error ≈ 0.14%, confirming the fit generalises within the sampled domain and is
not overfitting.

## Caveats

- The polynomial is intended for the sampled input range (`s1, s2 ∈ [0.005,
  0.1]`); like any polynomial surface it should not be extrapolated far outside
  it.
- `x` uses `s1 + s2` in the denominator, which is safely non-zero over the data.
