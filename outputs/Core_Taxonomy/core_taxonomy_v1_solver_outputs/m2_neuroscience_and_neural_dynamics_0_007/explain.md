# Synchronization Order Parameter vs. Coupling Strength

## Problem
A population of coupled neural oscillators is driven with increasing coupling
strength `K`, and the steady-state collective phase alignment — the
synchronization **order parameter** `r` — is measured. This is the classic
Kuramoto onset-of-synchrony picture: incoherence at weak coupling, a transition,
and macroscopic phase-locking that grows with `K`.

The task is to recover a closed-form `r = f(K)`.

## Data characterization
Loading `/app/data/train_data.csv` (4500 rows, `K ∈ [0.30, 8.00]`), the clean
`r` column is smooth and strictly monotonic in `K`. Three regimes are visible:

1. **Slow onset (K ≲ 0.5):** `r` is small and rises almost linearly
   (`r/K ≈ 0.069`).
2. **Transition (K ≈ 1–2):** `r` climbs steeply as the population locks.
3. **Saturation (K ≳ 4):** `r` levels off. A tail fit `r ≈ r∞ − c·K^(−3/2)`
   fits the region `K > 4` to RMSE ≈ 8×10⁻⁶ and gives a **sub-unity asymptote
   `r∞ ≈ 0.87`** — the order parameter does *not* approach 1 over the measured
   range, indicating a broadened (noisy / finite-population) transition rather
   than the idealized `r = √(1 − K_c/K)` result, which saturates to 1.

## Methodology
I tested a hierarchy of candidate forms:

- Mean-field Kuramoto closed forms `√(1 − K_c/K)` (Lorentzian frequencies) and
  the noiseless self-consistency integral for Gaussian/Lorentzian
  distributions: these rise far too fast toward `r = 1` and cannot match the
  gradual, sub-unity saturation (best RMSE ≈ 4×10⁻²).
- Sigmoidal / Hill / generalized-logistic forms: better (RMSE down to
  ≈ 2×10⁻³) but with structured residuals, especially near the onset.
- **Rational (Padé) functions** of `K`: these capture all three regimes
  cleanly. A degree-(4,4) rational reaches RMSE ≈ 7×10⁻⁵.

The adopted law is the degree-(4,4) rational

```
        n0 + n1 K + n2 K^2 + n3 K^3 + n4 K^4
r(K) = --------------------------------------
        1  + d1 K + d2 K^2 + d3 K^3 + d4 K^4
```

fitted by nonlinear least squares over all 4500 rows.

### Fitted parameters
| coeff | value            |    | coeff | value            |
|-------|------------------|----|-------|------------------|
| n0    |  0.009370361818  |    | d1    | −0.495517194134  |
| n1    |  0.038719929569  |    | d2    |  0.398379946140  |
| n2    | −0.046837127586  |    | d3    |  0.061400738068  |
| n3    |  0.037791728713  |    | d4    |  0.166344241811  |
| n4    |  0.144880390965  |    |       |                  |

## Why this form is well-behaved
- **Asymptote:** as `K → ∞`, `r → n4/d4 = 0.8710`, matching the empirical
  saturation value `r∞ ≈ 0.87`.
- **Pole-free:** the denominator's roots are all complex
  (`≈ −0.965 ± 1.706i`, `0.780 ± 0.977i`), so `r(K)` is finite and smooth for
  every real `K > 0`.
- **Monotonic:** `r(K)` increases monotonically across `K ∈ [0.25, 9]`, as the
  physics requires.

## Fit quality
- RMSE over the training set: **6.9×10⁻⁵**
- Maximum absolute residual: **5.2×10⁻⁴** (at the smallest `K = 0.30`)

The residual noise column `r_noisy` has scatter ≈ 10⁻², so the deterministic
fit is well inside the intrinsic measurement noise.

## Implementation
`/app/law.py` evaluates the two polynomials by Horner's method and returns
`r = N(K)/D(K)` for each input row independently, using only the declared
variable `K` and the fixed fitted constants — no state, I/O, ordering
dependence, or interpolation.
