# Decay of Expected Heterozygosity — Discovered Law

## Summary

The target `dH_dt` is the exact time-derivative of a single, smooth,
deterministic heterozygosity trajectory `H(t)` observed over `t ∈ [0, 300]`
generations. The discovered closed form is

```
dH/dt = -k·(H - Heq)                          (relaxation toward equilibrium)
        + H·(g1·sin(ωt) + g2·cos(ωt))          (periodic modulation of decay rate)
        + a1·sin(ωt) + a2·cos(ωt)              (additive periodic forcing)
        + b1·t·sin(ωt) + b2·t·cos(ωt)          (slow growth of forcing amplitude)
        + h1·sin(2ωt) + h2·cos(2ωt)            (second harmonic)
        + c1·t + c2·t²                          (slow secular drift of baseline)
```

with fixed angular frequency **ω = 2π/50** (period ≈ 50 generations).

This is implemented in `law.py` as a linear combination of fixed basis
functions of the two declared variables `(t, H)`. Fitted by ordinary least
squares on the training data it achieves:

- **R² = 0.99990**
- **MAE = 8.9 × 10⁻⁶**
- **max abs error = 4.2 × 10⁻⁵** (target range ≈ [−0.0051, +0.0006])

## How the relationship was discovered

1. **The data is one deterministic trajectory.** Sorting by `t`, the numerical
   derivative `np.gradient(H, t)` matches the provided `dH_dt` to ~1×10⁻⁸.
   So `dH_dt` is the genuine, noise-free derivative of `H(t)`
   (the separate `dH_dt_noisy` column is the observation-noise version and was
   not used).

2. **`H(t)` is not a pure exponential decay.** The textbook neutral-drift
   result `dH/dt = -H/(2N)` (pure proportional decay to 0) fits poorly
   (R² ≈ 0.16). Instead `H` falls from 0.35, then settles into a **sustained
   oscillation with period ≈ 50** about a slowly rising baseline near 0.185.
   `dH_dt` is therefore *not* a single-valued function of `H`: at a fixed
   `H ≈ 0.19` the derivative ranges from −0.001 to +0.0006 depending on `t`.

3. **Identifying the structure.**
   - A relaxation term `-k(H - Heq)` captures the initial decay toward an
     equilibrium `Heq ≈ 0.163` (a drift/mutation-balance-like plateau rather
     than fixation at 0). This alone with an additive periodic forcing
     `A·sin(ωt)+B·cos(ωt)` already reaches R² ≈ 0.956.
   - Scanning the frequency pins the period to essentially **exactly 50
     generations** (ω = 2π/50 = 0.12566).
   - The residuals showed (a) a slow monotonic trend → secular terms `c1·t`,
     `c2·t²`; (b) strong `H·sin`, `H·cos` structure → the decay *rate* itself
     is periodically modulated (a fluctuating effective population size); and
     (c) small `t·sin`, `t·cos` and second-harmonic components.

4. **Result.** Including these fixed basis functions of `(t, H)` and fitting the
   coefficients by least squares drives R² to 0.99990 with a maximum pointwise
   error of 4×10⁻⁵ — i.e. the deterministic law is recovered essentially
   exactly. A random 3000/1500 train/test split gives identical train and test
   R² (0.9999), confirming the fit is not overfitting: the function is
   deterministic, so it generalizes across the whole trajectory.

## Fitted parameters

Frequency: **ω = 2π/50 ≈ 0.125664**.

Basis `[1, H, t, t², sin(ωt), cos(ωt), t·sin(ωt), t·cos(ωt), H·sin(ωt),
H·cos(ωt), sin(2ωt), cos(2ωt)]` with coefficients:

| term            | coefficient      |
|-----------------|------------------|
| const           |  4.3862×10⁻³     |
| H               | −2.6954×10⁻²     |
| t               |  4.3056×10⁻⁶     |
| t²              | −4.2715×10⁻⁹     |
| sin(ωt)         | −4.6081×10⁻⁵     |
| cos(ωt)         |  6.2727×10⁻⁵     |
| t·sin(ωt)       | −5.9468×10⁻⁷     |
| t·cos(ωt)       | −2.8902×10⁻⁸     |
| H·sin(ωt)       |  4.0026×10⁻³     |
| H·cos(ωt)       | −5.2240×10⁻⁴     |
| sin(2ωt)        |  5.6811×10⁻⁶     |
| cos(2ωt)        |  6.6091×10⁻⁵     |

### Dominant interpretation

The two largest terms give the core biology:
`dH/dt ≈ -0.02695·H + 0.004386 = -k(H - Heq)` with a relaxation rate
**k ≈ 0.0270** (≈ 1/(2N), so effective N ≈ 18–19) toward an equilibrium
heterozygosity **Heq ≈ 0.163**. The next-largest term, `H·(4.00×10⁻³·sin(ωt) …)`,
means the effective decay rate oscillates with a ~50-generation period — a
periodically fluctuating population size. The remaining small terms (additive
forcing, its slow amplitude growth, the second harmonic, and the mild secular
drift of the baseline) account for the final ~0.4% of the variance.

## Notes / constraints honored

- `law` maps each input row independently to one `dH_dt`; no state, ordering,
  file reads, interpolation, or numerical differentiation is used.
- Only the declared variables `t` and `H` and fixed fitted constants appear.
