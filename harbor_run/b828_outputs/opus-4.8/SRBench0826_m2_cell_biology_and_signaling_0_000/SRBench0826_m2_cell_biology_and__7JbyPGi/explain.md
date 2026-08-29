# Discovering the growth law for contact-inhibited cell proliferation

## Problem

A population of mammalian cells grows in a nutrient-rich dish with limited
attachment surface. We must recover the instantaneous growth rate `dN_dt` as an
explicit, pointwise function of the observed variables `t, N, S, A`. The hidden
test set is the **right-hand (later-time) segment** of the same experiment, so
the law must **extrapolate toward confluence**, not merely interpolate.

## Data reconnaissance

The single trajectory (4500 rows, `t ∈ [0, 270]`) shows the classic sigmoidal
signature:

| quantity | behaviour |
|----------|-----------|
| `N`      | rises monotonically 1000 → 47 896, saturating |
| `dN_dt`  | rises, peaks (~329) near `N ≈ 18 800`, then decays toward ~28 |
| `S`      | rises monotonically 0 → 4755 |
| `A`      | jumps up early (10 → ~37), then decays monotonically to ~2.045 |

Because `N` is monotone in `t`, **every column is a function of `t` on this one
trajectory**, so naive multi-variable regression trivially reaches R² ≈ 0.9999
by exploiting trajectory correlations — but such a fit fails on the extrapolated
test segment. The task is to find the *true* pointwise law.

### The auxiliary variables are slaved sub-systems

Numerical differentiation of the auxiliary columns revealed exact, clean ODEs:

- **`dS/dt = 0.01·N − 0.1·S`** (R² = 1.000 to machine precision). `S` is a
  low-pass "crowding signal" tracking `N`; at quasi-steady state `S ≈ 0.1·N`.
- **`dA/dt = 10 − 0.1·A − 10⁻⁴·N·A`** (R² ≈ 0.99999). Its quasi-steady value is
  `A* = 10⁵/(1000 + N)`, which reproduces the observed confluent residual
  `A → 10⁵/(1000+47896) ≈ 2.045`. `A` is the **instantaneously available
  attachment space**: replenished at a constant rate and consumed in proportion
  to the number of cells occupying it.

These exact round-number constants confirm the dataset is noise-free and
generated from a designed coupled ODE system.

## Identifying the growth law

The initial transient (`t < 15`), where `A` and `S` have **not yet** relaxed to
their `N`-slaved values, is the key discriminator: it is the only place where
the variables are mutually independent. Fitting candidate forms on the
quasi-steady region (`t > 50`) and predicting the transient separates the true
functional dependence from trajectory artefacts.

Systematic search over interpretable growth families (logistic, Gompertz,
Richards/θ-logistic, Monod, and space-modulated products), scored both by
overall fit **and by genuine extrapolation beyond the training range**, singled
out:

```
dN/dt = r · N · (1 − N/K)^p · A/(A + c)
```

- `r · N` — intrinsic exponential proliferation.
- `(1 − N/K)^p` — density-dependent crowding relative to the maximum confluent
  capacity `K`. The exponent `p ≈ 0.87 < 1` skews the growth curve so peak
  growth occurs at `N ≈ 19 000` (well below `K/2`), matching the data and the
  observed near-confluence curvature (the local tail behaves as
  `dN/dt ∝ (K − N)^0.8`, not the `^1` of ordinary logistic).
- `A/(A + c)` — saturating (Monod) dependence on available space: ~1 when space
  is plentiful, throttling growth as `A` collapses at confluence.

Both factors encode "how growth depends on remaining available space," from two
complementary angles (global density and instantaneous free area).

### Fitted parameters (all training rows)

| param | value | meaning |
|-------|-------|---------|
| `r`   | 0.04788957 | intrinsic per-capita rate (1/time) |
| `K`   | 48933.03   | maximum confluent density (cells) |
| `p`   | 0.87227332 | crowding-response exponent |
| `c`   | 4.02530017 | half-saturation available-space constant |

## Validation

- **Full-data fit:** R² = 0.99989, RMSE = 1.08 (over a `dN_dt` range of ~28–329).
- **Extrapolation (the real test scenario).** Fitting only on low-`N` data and
  predicting the withheld high-`N` tail:

  | train region | test RMSE (this law) | test RMSE (pure-N Richards) |
  |--------------|----------------------|------------------------------|
  | `N < 44000`  | 2.75 | 3.17 |
  | `N < 45000`  | 0.97 | 1.95 |
  | `N < 46000`  | 0.62 | 1.02 |

  The space-modulated law extrapolates toward confluence better than a
  pure-`N` Richards curve, because its fractional tail exponent matches the true
  approach to the carrying capacity.

## Why `t` and `S` are excluded

`t` must not appear in an autonomous mechanistic rate law, and it added nothing.
`S` is a redundant low-pass image of `N` (`dS/dt = 0.01N − 0.1S`); including it
only reproduced trajectory correlations that break under extrapolation. The
instantaneous growth rate is fully explained by the current population `N` and
the current available space `A`.

## The law

```python
dN/dt = 0.04788957 · N · max(0, 1 − N/48933.03)^0.87227332 · A/(A + 4.02530017)
```

Implemented pointwise in `law.py`, mapping each row independently (with a guard
that the crowding factor is zero once `N ≥ K`, since growth cannot exceed the
carrying capacity and a fractional power of a negative number is undefined).
