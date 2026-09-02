# Discovering R0(c, D)

## Task
Recover a closed-form expression predicting the reproduction quantity `R0` from
the average contact rate `c` and the infectious period `D`, using the training
set `/app/data/train_data.csv` (4500 rows; columns `c`, `D`, `R0`, plus a noisy
copy `R0_noisy` which was ignored — the clean `R0` is the target).

## Exploratory findings
Ranges: `c ∈ [1, 30]`, `D ∈ [1, 20]`, `R0 ∈ [0.36, 3.62]`.

Binning the data revealed the qualitative shape of the surface:

- **R0 is non-monotonic (humped) in both drivers.** Holding one variable fixed,
  `R0` rises, peaks near `c ≈ 6` and `D ≈ 6` (peak value ≈ 3.5), then declines.
- The decline in `c` is much stronger than in `D` (marginally, `corr(R0, c) ≈ -0.88`
  while `corr(R0, D) ≈ 0`, the latter only because the D-hump sits mid-range).
- There is a genuine **c–D interaction**: the rate at which `R0` falls off in `c`
  grows with `D`. A purely separable model `f(c)·g(D)` reaches only R²≈0.92 in
  log-space; adding interaction is essential.

## Model search
I tested many compact algebraic / transcendental families by nonlinear
least squares (linear space) and linear least squares (log space):

| Family | R² |
|---|---|
| power law `A·cᵃ·Dᵇ` | 0.54 |
| `A·c^m·D^n·exp(−a c − b D)` | 0.94 |
| `A·c^m·D^n·exp(−a c − b D − g cD)` | 0.991 |
| rational `A cD /(1+…)` forms | ≤ 0.88 |
| stretched-exp / harmonic / ratio forms | ≤ 0.95 |
| Gaussian in logs (quadratic in ln c, ln D) | 0.988 |
| **polynomial in (ln c, ln D)** | see below |

No compact 3–5 parameter algebraic or exponential form exceeded R²≈0.99 — the
turn-over and the interaction are too rich for those. However, `ln R0` is a very
smooth function of `u = ln c` and `v = ln D`, and a polynomial surface in those
coordinates converges rapidly and — importantly — **generalizes** on held-out
data (random 3600/900 split):

| degree | #terms | test mean rel. err | test max rel. err | test R² |
|---|---|---|---|---|
| 3 | 10 | 0.94% | 8.0% | 0.99952 |
| 4 | 15 | 0.34% | 5.7% | 0.99993 |
| **5** | **21** | **0.10%** | **0.83%** | **0.999995** |
| 6 | 28 | 0.05% | 0.34% | 0.999998 |

The steady out-of-sample improvement with degree (no overfitting blow-up)
confirms the surface is intrinsically a smooth log-response rather than a
low-order polynomial; degree 5 was chosen as an excellent accuracy/parsimony
balance.

## Final law
With `u = ln(c)`, `v = ln(D)`:

```
ln R0 = Σ_{i+j ≤ 5} a_ij · u^i · v^j
R0    = exp(ln R0)
```

Fitted by OLS on `ln R0` over the full training set. The dominant terms are

```
a_00 ≈ -1.002,  a_10 ≈ 1.047,  a_01 ≈ 0.980
```

so to leading order **R0 ≈ e⁻¹ · c · D**, i.e. reproduction scales with the
expected number of contacts made while infectious (`c·D`). The remaining
higher-order coefficients encode the empirical **saturation and turn-over**: the
effective transmission contribution per contact declines as contact rate and
infectious period grow (and does so faster jointly, via the mixed `u^i v^j`
terms), producing the observed peak near `c ≈ D ≈ 6` and the decay beyond it.
Population structure is held fixed and enters only through the constant term.

Full coefficient list (exponent pair `(i,j)` → `a_ij`) is embedded in
`/app/law.py`.

## Accuracy of the submitted `law`
On the full training set: **R² = 0.999995**, mean relative error **0.10%**,
99th-percentile relative error 0.37%, max relative error 1.4%.

## Method notes / constraints
- `law([row])` maps each row independently: it computes `u, v` from that row's
  `c, D` and evaluates the fixed polynomial. No state between calls, no data
  reads, no interpolation/lookup, no ordering dependence — only `c`, `D` and the
  constant fitted coefficients are used.
- Valid for the training domain `c ∈ [1, 30]`, `D ∈ [1, 20]`; as with any
  polynomial surface, extrapolation far outside this range is not recommended.
