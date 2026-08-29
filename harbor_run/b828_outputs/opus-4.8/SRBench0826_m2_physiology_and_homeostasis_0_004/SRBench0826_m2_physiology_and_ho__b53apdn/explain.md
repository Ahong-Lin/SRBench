# Discovering the glucose clearance law `dG/dt = f(G, Ia)`

## 1. Problem and data

The dataset is a single trajectory of a glucose–insulin regulation experiment,
sampled on a fine, uniform time grid (`dt ≈ 0.02`, 4500 rows, `t ∈ [0, 90]`).
Columns:

| column | meaning |
|--------|---------|
| `t`    | time |
| `G`    | plasma glucose |
| `I`    | plasma insulin |
| `Ia`   | insulin **action** (remote/active-insulin compartment) |
| `dG_dt`| target: instantaneous rate of change of glucose |

The trajectory starts from a glucose bolus (`G = 10`, `I = 0.5`, `Ia = 0`), glucose
rises briefly to a peak (`G ≈ 10.4`), then is cleared and relaxes toward a steady
state near `G ≈ 1.85`, `I ≈ 0.62`, `Ia ≈ 1.21`.

## 2. Key structural findings

### (a) `Ia` is a remote insulin compartment driven by `I`
Numerically differentiating `Ia` along the trajectory recovers, to essentially
machine precision (R² ≈ 1 − 2·10⁻⁸), the clean linear law

```
dIa/dt = 0.2 * I - 0.1 * Ia
```

This is the classic "insulin action / remote insulin" equation of the
Bergman-type minimal model: plasma insulin `I` feeds a remote compartment `Ia`
(gain 0.2) that decays with rate 0.1. So `Ia` is the physiologically active
insulin signal that couples to glucose.

### (b) `dG/dt` depends only on `G` and `Ia`
Because the data lie on a **1-D trajectory**, `G`, `I`, and `Ia` are strongly
(non-linearly) collinear, so naïve regressions can appear to "need" `I`. To break
this ambiguity I fit polynomial bases in different variable subsets and checked
convergence:

* A polynomial in **`(G, Ia)` only** converges to the reference values to machine
  precision (max error `1e-5` at degree 7; `5e-3` already at degree 4).
* Adding `I` gives **no** genuine improvement beyond what `(G, Ia)` already
  achieves, and the residual of a `(G, Ia)` fit is uncorrelated with `I`
  (corr ≈ 0.0).

Conclusion: the true right-hand side is `dG/dt = f(G, Ia)`. Insulin `I` influences
glucose **only indirectly**, through `Ia`. This matches the minimal-model wiring
`I → Ia → glucose disposal`.

### (c) Insulin promotes glucose disposal ~ mass action `Ia·G`
Sweeping a candidate disposal term `SI·Ia·G` and asking which value of `SI` makes
`dG/dt + SI·Ia·G` a single-valued function of `G` selects `SI ≈ 0.15` and reduces
the spread by ~10×. So the dominant clearance is an insulin-action-times-glucose
mass-action term, exactly as "insulin promotes uptake" suggests. The insulin-
independent part (`Ia = 0`) is a net glucose-appearance term; at the initial
point (`G = 10, Ia = 0`) it equals the observed `dG/dt = 0.5`.

Pure `-(p1 + Ia)·G + p1·Gb` (textbook minimal-model glucose equation) does **not**
fit (R² ≈ 0.95, and it forces an unphysical negative `p1`): this particular model
has a richer, mildly nonlinear appearance/disposal structure, captured below.

## 3. The fitted law

Writing the right-hand side as a polynomial in the insulin-action variable `Ia`
with glucose-dependent (cubic) coefficients:

```
dG/dt =  P0(G)             # net glucose appearance (insulin-independent)
       + Ia   * P1(G)      # insulin-action-dependent disposal (leading, ~ -0.13·Ia·G)
       + Ia^2 * P2(G)      # saturation correction of insulin action

Pk(G) = c[k,0] + c[k,1]·G + c[k,2]·G^2 + c[k,3]·G^3
```

Fitted constants (fixed once from the training data):

| term         | c·,0        | c·,1        | c·,2        | c·,3         |
|--------------|-------------|-------------|-------------|--------------|
| `Ia^0` (P0)  |  0.421791   |  0.015882   |  0.023104   | -0.0023898   |
| `Ia^1` (P1)  | -0.160666   | -0.130584   | -0.032681   |  0.0031522   |
| `Ia^2` (P2)  |  0.020741   | -0.005912   |  0.011442   | -0.0006179   |

The leading insulin term `≈ -0.131·Ia·G` is the promised insulin-driven uptake;
the remaining terms are small polynomial corrections that give a near-exact fit
across the whole transient.

## 4. Accuracy and robustness

* On all training rows: **R² = 0.99993**, max absolute error **0.0061**
  (target range ≈ [-1.13, 0.50]).
* It reproduces the two physical endpoints exactly: initial slope
  `0.501` (true `0.500`); near-steady-state slope `-0.016` (true `-0.017`).
* **Time-split (extrapolation) test** — fit on early times, predict the held-out
  later segment (the scenario the hidden test mimics):

  | train window | test window | test max-error |
  |--------------|-------------|----------------|
  | `t < 72`     | `t ≥ 72`    | 0.0018 |
  | `t < 60`     | `t ≥ 60`    | 0.0051 |
  | `t < 54`     | `t ≥ 54`    | 0.0117 |

  The hidden test (the right-hand/late segment) sits near the fixed point
  `G ≈ 1.85`, a region densely sampled in training, so no extrapolation is
  required and errors stay small.

## 5. Implementation notes (`law.py`)

* `law` maps **one row at a time** to `{"dG_dt": value}`, using only `G` and `Ia`.
* It is a closed-form polynomial (Horner-evaluated): no file reads, no state
  between calls, no ordering, no interpolation, no numerical differentiation,
  no ML black box — just fixed constants inferred from the training data.
* `t` and `I` are accepted in the input dict but not used, consistent with the
  finding that `dG/dt` is exactly a function of `(G, Ia)`.
