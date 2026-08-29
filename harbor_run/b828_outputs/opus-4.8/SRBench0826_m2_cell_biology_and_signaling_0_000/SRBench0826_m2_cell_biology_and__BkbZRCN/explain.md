# Discovering the growth law for a contact-inhibited cell population

## Target

Predict the instantaneous rate `dN_dt` (cells per unit time) from the observed
state `(t, N, S, A)`. The hidden test set is the **right-hand time segment** of
the same experiment, i.e. later times where the culture is close to confluence.

## Data overview

| var | meaning (inferred) | range in train |
|-----|--------------------|----------------|
| `t` | time | 0 → 270 |
| `N` | cell count | 1000 → 47 896 (monotonically increasing) |
| `S` | slow "sensed" density (low-pass filtered N) | 0 → 4755 |
| `A` | available attachment space | starts 10, rises to ≈39, decays to ≈2.05 |
| `dN_dt` | growth rate | rises to ≈329 near t≈96, then decays |

`dN_dt` traces the classic bell shape of logistic growth, and it matches the
numerical derivative of `N` to 1e-6, so the data are essentially noiseless and
internally consistent.

## Reverse-engineering the generating model

Because the whole record is a **single trajectory**, `N`, `S`, `A` are all
monotone-or-smooth functions of `t`, so along this curve many formulas fit the
training points equally well. To find the *true* pointwise law (the only thing
that extrapolates to the held-out right segment) I reconstructed the underlying
ODE system by fitting each state's time-derivative to simple candidate forms.

Two of the three right-hand sides turned out to be **exact** (residual ≈ 0):

* **S dynamics** — a first-order low-pass filter of the density:

  `dS/dt = 0.01·N − 0.1·S`   (S relaxes toward its quasi-equilibrium 0.1·N; this is why S/N → 0.1)

* **A dynamics** — available space is replenished, decays, and is consumed by cells:

  `dA/dt = 10 − 0.1·A − 1e-4·N·A`
  (equilibrium `A* = 10 / (0.1 + 1e-4·N) = 100/(1+0.001·N)`, which is ≈2.04 at
  N≈48 000 — matching the observed floor of A; A overshoots early because it
  lags this shrinking target.)

These clean discoveries confirm the dataset comes from a deliberate mechanistic
model, and they explain the roles of `S` (delayed crowding signal) and `A`
(free surface area).

## The growth law `dN/dt`

I tested a large family of pointwise forms for `dN_dt` as functions of
`(N, S, A)` — mass-action in space (`r·N·A`), Monod/Hill saturation in `A`,
logistic and Richards in `N` and in `S`, linear inhibition (`r·N − c·S`),
products and ratios, and sparse polynomial (SINDy-style) libraries.

Key findings:

* `dN_dt` is **not** proportional to available space `A` (`r·N·A` gives RMSE ≈ 98).
  The per-capita rate `dN_dt/N` is *not* a single-valued function of `A`
  (it takes different values on the rising and falling branches of `A`), so no
  `f(A)` law is correct.
* The best-fitting **and best-extrapolating** form is a **generalized-logistic
  (Richards / theta-logistic) law in N**:

  **`dN/dt = r · N · ( 1 − (N/K)^ν )`**

  with `r = 0.08437`, `K = 49298.6`, `ν = 0.23935`.

### Why Richards in N, and not a form using S or A

The A/S-based correction terms lower the *overall* training RMSE slightly (they
absorb the small early per-capita "bump" caused by the lag of S and the
overshoot of A), but they **overfit that transient and damage extrapolation**.
I validated this with a time-ordered holdout: fit on the left 85 % of the
trajectory, predict the far-right 5 % (the analogue of the real test set):

| model | far-right 5 % RMSE | far-right max error |
|-------|-------------------:|--------------------:|
| **Richards(N)** | **0.51** | **0.66** |
| Richards(N)·(1+cA) | 4.68 | 5.06 |
| logistic(N)·A/(c+A) | 10.6 | 11.3 |
| Richards(S) | 3.78 | 3.83 |
| plain logistic(N) | 48.4 | 50.3 |

Richards(N) is dramatically the most reliable near carrying capacity — exactly
the regime the hidden test occupies. On the full training set its RMSE is 4.44
(mean relative error 2.6 %), with the misfit concentrated entirely in the early
low-density transient (t≲130); over the last 300 training rows the RMSE is only
0.16 and the residual shrinks to ≈0 at the end of the record, so continuation
past t=270 is accurate.

### Interpretation

`1 − (N/K)^ν` is the fraction of proliferative capacity still available as the
dish fills. `ν < 1` makes contact inhibition bite early but relax the growth
rate gently as `N → K` — an asymmetric approach to the confluent density `K ≈
49 300`, consistent with space-limited, contact-inhibited mammalian cell growth.

## Submitted law

`law()` in `law.py` implements, per row independently:

```
dN_dt = 0.08436579453 · N · ( 1 − (N / 49298.61346) ^ 0.2393498501 )
```

using only the declared variable `N` and constants fit from the training data —
no interpolation, lookup, ordering, or cross-row state.
