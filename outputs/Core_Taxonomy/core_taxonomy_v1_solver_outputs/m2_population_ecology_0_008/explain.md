# Discovered Law: Per-capita growth `g` vs. resource supply `S`

## Summary

The measured per-capita growth response is **non-monotonic** in supply `S`:

- it is **slightly negative** at very low supply (`g(0.1) ≈ -0.115`) — net loss,
- crosses zero near `S ≈ 0.22`,
- rises through a broad **hump that peaks near `S ≈ 9–12`** (`g_max ≈ 1.31`),
- and then **decays back toward zero** at high supply (`g(100) ≈ 0.002`).

This shape is captured by a **three-component power × exponential ("gamma / Ricker") kinetic model**:

```
g(S) =  A1 · S^p1 · exp(-k1·S)      (slow-decaying baseline, carries the tail)
      + A2 · S^p2 · exp(-k2·S)      (opposing term, sets the low-S negative dip)
      + A3 · S^p3 · exp(-k3·S)      (S^3 growth kernel → dominant hump)
```

## Fitted parameters

| term | amplitude `A` | exponent `p` | decay `k` | role |
|------|--------------:|-------------:|----------:|------|
| 1 | `+2.633078` | `-0.022434` | `0.072304` | near-constant prefactor, slow decay → controls the far tail |
| 2 | `-2.598700` | `-0.052247` | `0.223874` | opposing near-constant term, faster decay → creates the low-`S` net-loss dip |
| 3 | `+0.003779` | `+2.990746` | `0.237035` | `S³` growth kernel with moderate decay → the main growth hump |

Interpretation notes:

- Terms 1 and 2 have prefactor exponents very close to `0` (`S^-0.02`, `S^-0.05`), so they act
  essentially as a **difference of two decaying exponentials**. Their near-cancellation at low
  supply produces the small negative growth (maintenance/loss exceeding uptake), while the
  slower-decaying term 1 dominates the high-supply tail.
- Term 3 has exponent `p3 ≈ 3.0`, i.e. an `S³·exp(-k3·S)` kernel that peaks around
  `p3/k3 ≈ 3/0.237 ≈ 12.6` and supplies most of the hump amplitude.
- The **effective response is a decelerating power at intermediate supply** (the local
  log–log slope of `g` drops below 1 across the mid-range, consistent with the "diminishing
  returns" description), while inhibition/limitation causes the eventual decline at high supply.

## Methodology

1. **Data inspection.** Loaded `/app/data/train_data.csv` (4500 rows, `S ∈ [0.1, 100]` on a
   log-spaced grid). The clean target `g` traces a smooth hump with a low-`S` negative region
   and a long decaying tail. The provided `g_noisy` column indicated an observation noise level
   of `std ≈ 0.0099`.

2. **Form search.** Tested a large family of closed forms with `scipy.optimize.curve_fit`:
   - pure/decelerating power laws `a·S^b` (fail — data is non-monotonic),
   - log-normal / polynomial-in-log(S) (poor — response is not symmetric in log S),
   - single Ricker/gamma `a·S^b·exp(-c·S)` and stretched-exponential variants
     `a·S^b·exp(-c·S^q)` (good backbone, `R² ≈ 0.996–0.9996`, but leaves a systematic
     residual wave and cannot match both the mid-range and the heavy tail),
   - multi-term power×exponential sums.

3. **Selection.** The three-term power×exponential model resolved the residual wave and reached
   `R² = 0.99995`. It was validated on a random **50/50 train/test split**: test `R² = 0.999952`
   ≈ train `R² = 0.999616`… (test ≈ train), confirming genuine structure rather than overfitting.
   Final parameters were then re-fit on the full dataset.

## Fit quality (full training set)

- `R² = 0.9999526`
- `RMSE = 0.00321` (below the observation noise level `≈ 0.0099`)
- `max |residual| = 0.0061`

Residuals are small and unbiased across the full supply range. Relative error is only large in
the far tail (`S ≳ 70`) where `g` itself is `~10⁻³`, but the absolute error there stays `≲ 3·10⁻⁴`.

## Implementation

`/app/law.py` implements `g(S)` exactly as the three-term expression above, mapping each input
row independently to one prediction (no state, no data access, only the variable `S` and the
fixed fitted constants).
