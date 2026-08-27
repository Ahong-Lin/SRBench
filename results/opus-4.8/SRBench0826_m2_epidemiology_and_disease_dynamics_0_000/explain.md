# Discovering the law for `dI_dt`

## 1. Setup

The data describe a closed outbreak of a novel respiratory pathogen with
compartments **S** (susceptible), **E** (exposed), **I** (infectious) and
**R** (recovered). The population is closed:

```
N = S + E + I + R = 1000   (constant to 1e-12 over the whole dataset)
```

The target is `dI_dt`, the instantaneous rate of change of the infectious
pool. A first sanity check confirmed that `dI_dt` really is the time
derivative of the `I` column: comparing it against a numerical derivative
of `I(t)` gives correlation `0.99999997` (max abs difference ~8e-4, i.e.
pure finite-difference error). So we are looking for the right-hand side
of the ODE that generated the `I` trajectory.

## 2. What the data rule out

**It is not the textbook SEIR law `dI/dt = σE − γI`.**
At `t = 0` the state is `S=999, E=0, I=1` and yet `dI_dt = +0.146 > 0`.
The textbook law gives `σ·0 − γ·1 = −γ < 0` there — the wrong sign. A
direct least-squares fit of `dI_dt` to `{E, I}` only reaches `R² = 0.61`
and returns *negative* `σ`. So `I` cannot be fed purely by maturation of
`E`; it must be driven directly by contact with susceptibles.

**Transmission is driven by `I`, and is non-linear.** Fitting the
(smoothed) derivative of `S` is extremely clean and reveals a nonlinear
incidence:

```
dS/dt = −0.499·(S·I/N) + 0.456·(S·I²/N²)      (R² = 0.9999999)
```

i.e. a mass-action term with a saturation/behavioural correction at high
prevalence. `E` adds nothing to `dS/dt`, so only `I` transmits.

**`dI_dt` is essentially a function of `S` and `I`.** A full polynomial in
`(S, I)` alone reaches `R² = 1.0` (degree 4), while adding `E` or `R`
brings no further improvement in-sample. This is the fingerprint of a
chain in which infection flows **directly into `I`**, and `I` then drains
onward (toward `E`/`R`). Consistently, the recovered pool grows from the
`E` compartment (`dR/dt ≈ 0.293·E`, `R² = 0.993`), and `I` peaks *before*
`E` (t≈28.9 vs t≈32.1) — the opposite ordering to a classical S→E→I→R
chain.

## 3. The law

Writing the derivative as `I` times a per-capita growth rate, and doing a
stability-guided sparse regression over physically-motivated monomials,
one form stands out:

```
dI/dt = I · [ c0 + c1·(S/N)² + c2·(S/N)·(I/N) + c3·(E/N) ]
```

with fitted coefficients (OLS on the full training set):

| coeff | term            | value      |
|-------|-----------------|------------|
| c0    | 1 (baseline)    | −0.092991  |
| c1    | (S/N)²          | +0.331666  |
| c2    | (S/N)·(I/N)     | −1.725593  |
| c3    | (E/N)           | +0.360502  |

### Why this form

- **`dI/dt ∝ I`.** Every term carries a factor `I`, so `dI/dt → 0` as
  `I → 0`. This is the essential physical constraint and is exactly what
  makes the model behave correctly in the tail of the epidemic, where the
  test set lives.
- **Per-capita growth rate** `g = c0 + c1(S/N)² + c2(S/N)(I/N) + c3(E/N)`
  is positive while susceptibles are plentiful (early growth) and turns
  negative once `S` is depleted (the decline), reproducing the rise → peak
  → decay shape. The `(S/N)²` dependence (rather than plain `S/N`) is what
  the data demand: it is the single change that keeps extrapolation to the
  far tail accurate.
- **`E` enters weakly and positively** (`c3`), reflecting the coupling
  between the exposed pool and the infectious dynamics late in the
  outbreak, when `S` is nearly frozen and `E` carries the decay
  information.

## 4. Fit quality and validation

- **In-sample:** `R² = 0.99975`, `RMSE = 0.0278`, max abs error `0.091`
  (signal std ≈ 1.75).
- **Coefficient stability:** refitting on 60%, 80% and 100% of the
  trajectory changes the coefficients by less than `0.009`. A
  well-specified structural form has (nearly) data-independent
  coefficients; an overfit one does not.
- **Forward extrapolation (the important test).** The hidden test set is
  the *right-hand time segment* of the same experiment, so it extrapolates
  beyond the training range (later times, smaller `S`, `E`, `I`). To
  mimic this I trained on the first 70% and scored on the last 15% (the
  flattest tail, `S ≈ 300`, `I,E → 0`):
  - this model: **far-tail `R² = 0.9998`**;
  - a plain degree-4 polynomial in `(S, I)`: `0.996` (and degree ≤ 3
    polynomials diverge, `R² < 0`), because they lack the `dI/dt ∝ I`
    structure and blow up outside the fitted range.

The chosen form combines the best in-sample fit, the best far-tail
extrapolation, and by far the most stable coefficients — the combination
we want for predicting the held-out declining phase.

## 5. Implementation

`law.py` computes `N = S+E+I+R` per row (robust to any scaling), forms the
four features above and returns
`dI_dt = I·(c0 + c1·(S/N)² + c2·(S/N)(I/N) + c3·(E/N))`.
Running `python law.py` reproduces `R² = 0.999749`, `RMSE = 0.027751` on
the training data.
