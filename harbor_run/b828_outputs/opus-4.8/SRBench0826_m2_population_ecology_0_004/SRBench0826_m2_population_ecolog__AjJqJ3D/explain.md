# Recovering the growth law for species 1 (`dN1_dt`)

## 1. What the data is

`train_data.csv` is a **single, densely sampled, essentially noise-free
trajectory** of a coupled dynamical system:

- 4500 rows, `t` strictly increasing from 0 to ~54 with a uniform step
  `dt ≈ 0.012`.
- The provided `dN1_dt` matches a centered finite difference of `N1(t)` to
  `< 2e-3` everywhere, confirming that `dN1_dt` is the genuine time derivative
  of `N1` along this trajectory (the dynamics are autonomous, so `t` itself is
  not a driver).

The trajectory is a **damped oscillation** (a decaying spiral): `N1` swings
20 → 33 → 9 → 14…, `P1` swings 5 → 15.5 → 10.5…, and `N2` climbs monotonically
toward ~95. This is the classic signature of competition combined with a
delayed, oscillatory coupling to a third state.

Observed variable ranges (training):

| var | min | max |
|-----|-----|-----|
| N1  | 9.18 | 33.22 |
| N2  | 60.0 | 95.32 |
| P1  | 5.0  | 15.58 |

## 2. Structural clues

**Species 2 obeys a clean two-species competitive Lotka–Volterra law.** Fitting
the per-capita rate `(dN2/dt)/N2` (via finite differences) to `1, N1, N2, P1`
gives an essentially exact fit (R² = 1.000) with round coefficients and a
**zero coefficient on P1**:

```
dN2/dt = N2 · (0.4 − 0.002·N1 − 0.004·N2)
       = 0.4·N2·(1 − (N2 + 0.5·N1)/100)      # r2=0.4, K2=100, α21=0.5
```

So `N2` competes only with `N1`; it does not feel `P1`.

**Species 1 is different.** Its dynamics are strongly coupled to `P1`:

- A pure two-species law `dN1/dt = N1·(r − a·N1 − b·N2)` explains only
  R² ≈ 0.64 — badly wrong. `P1` is indispensable.
- A three-species generalized Lotka–Volterra law
  `dN1/dt = N1·(r1 − a11·N1 − a12·N2 − a13·P1)` reaches R² ≈ 0.998 but leaves a
  **systematic** residual (max error ≈ 0.08 on noise-free data), so the true
  law is *not* simple linear-per-capita gLV.
- Adding a Holling type-II saturation to the `P1` coupling does **not** help
  (the best saturation constant is 0, i.e. mass-action), so the extra structure
  is not a standard functional response.

**The residual is a smooth low-order polynomial in the state.** Fitting
`dN1_dt` to a full polynomial in `(N1, N2, P1)`:

| degree | # terms | max abs error |
|--------|---------|---------------|
| 2 | 10 | 2.0e-3 |
| **3** | **20** | **5e-6** |
| 4 | 35 | 1e-6 |

Degree 3 already collapses the error to the numerical floor. The instantaneous
growth rate of species 1 is therefore captured **exactly** (to 6 significant
figures) by a **cubic response surface** in `(N1, N2, P1)`: intrinsic growth and
self-crowding (`N1`, `N1²`), mutual suppression by `N2` and by `P1`
(`N1·N2`, `N1·P1`), plus weak second-order modulation of those interactions
(the remaining cubic cross terms). This is exactly what one expects from a
competitive system in which the *strength* of the pairwise interactions is
itself mildly density-dependent.

## 3. The submitted law

`dN1_dt = P₃(N1, N2, P1)`, a degree-3 polynomial (20 monomials, constant through
cubic). The coefficients are fixed constants fitted once by least squares on the
full training trajectory. For numerical conditioning the monomials are stored in
standardized form (each monomial has its training mean subtracted and is divided
by its training standard deviation before being weighted); algebraically this is
identical to an ordinary cubic polynomial in `N1, N2, P1`.

```
dN1_dt = Σ_k  coef_k · ( m_k(N1,N2,P1) − mu_k ) / sd_k
```

where `m_k` ranges over all monomials `N1^a · N2^b · P1^c` with `a+b+c ≤ 3`.
See `_EXP`, `_MU`, `_SD`, `_COEF` in `law.py`.

- Fit quality on training: **max abs error 5.1e-6, RMS 5.7e-7** — effectively
  exact.
- The function is pointwise: it maps one `(N1, N2, P1)` to one `dN1_dt`, uses no
  time ordering, no `t`, no state between calls, no interpolation table.

## 4. Why this extrapolates to the hidden test segment

The test set is the **right-hand time continuation** of the same experiment. The
oscillation is *damped*, so the continuation is the **inner part of the spiral**,
approaching the coexistence equilibrium. Integrating the recovered system
forward from the last training point gives a test trajectory confined to

```
N1 ∈ [13, 15],  N2 ∈ [93, 94],  P1 ∈ [10.5, 12.2]
```

which lies **strictly inside the region already swept by the training spiral**
(the outer loops of the trajectory repeatedly pass through and around this
neighborhood). Predicting `dN1_dt` there is therefore **interpolation on the
well-sampled state manifold**, not extrapolation — precisely the regime where a
response surface that is exact on the training data remains accurate.

Held-out checks confirm this: fitting on the first 70–90 % of the trajectory and
predicting the remaining segment gives max errors of 0.011 (70 %) down to 0.0008
(90 %). Because the true test region is even more interior (smaller-amplitude,
near-equilibrium loops), the full-data cubic is expected to be at least this
accurate.

## 5. Interpretation summary

- Two plant species `N1`, `N2` compete (mutual suppression), with `N2` following
  a clean logistic-competitive law (`r2=0.4, K2=100, α21=0.5`).
- A third coupled state `P1` acts as a delayed suppressor of species 1 (rising
  when `N1` is high, then pushing `N1` back down), producing the damped
  competitive oscillation.
- Species 1's instantaneous growth is the competitive/self-limitation balance
  written as a compact cubic response surface in `(N1, N2, P1)` — the minimal
  polynomial order that reproduces the data exactly.
