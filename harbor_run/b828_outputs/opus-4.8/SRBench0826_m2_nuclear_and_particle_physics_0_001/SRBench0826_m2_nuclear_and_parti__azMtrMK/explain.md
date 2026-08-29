# Discovering the law for `dNd_dt` in a parent → daughter → stable decay chain

## 1. Problem and data

We must predict the instantaneous daughter accumulation rate `dNd_dt` from the
observed state `(t, Np, Nd)` of a two-step radioactive decay chain

```
parent (Np)  --lambda_p-->  daughter (Nd)  --lambda_d-->  stable
```

The training set is a single, densely-sampled trajectory:
`t ∈ [0, 90]`, 4500 points, `dt ≈ 0.02`, with `Np(0)=10000`, `Nd(0)=0`.
The hidden test set is the **right-hand time segment** (larger `t`, i.e. the
deep tail) of the same experiment.

## 2. What the data tells us

**The parent decays exactly exponentially.**
A log–linear fit of `Np` gives

```
Np(t) = 10000 · exp(-0.1 · t)      (residual std ~1e-9)
```

so `lambda_p = 0.1` and, crucially, **`t` and `Np` are in one-to-one
correspondence** on the trajectory (`t = -10·ln(Np/10000)`). The whole time
dependence of the source term can therefore be written using `Np`.

**`Nd` and `dNd_dt` are mutually consistent and noise-free.**
The finite-difference derivative of `Nd` matches the reported `dNd_dt` to within
the expected O(dt) discretization error, and `Nd` is as smooth as the clean
parent curve (second differences ~0.009). So `dNd_dt` really is the exact
derivative of a smooth `Nd(t)`; there is no observation noise to fight.

**The daughter decay constant is clean: `lambda_d = 0.05`.**
In the deep tail the parent is negligible, so `dNd_dt → -lambda_d·Nd`.
Fitting `-dNd_dt = b·Nd + c·Nd² + a·Np` for `t > 70` gives `b = 0.04996…`
with a residual of `~1e-4`, and `-dNd_dt/Nd` converges to `0.0520` at the very
last samples. The daughter's own decay constant is therefore
**`lambda_d ≈ 0.050`**.

## 3. Why the textbook Bateman law does **not** fit

The classical two-step Bateman equation is linear:

```
dNd/dt = lambda_p·Np - lambda_d·Nd     (=> Nd is a sum of two exponentials)
```

This form is **rejected** by the data:

* At `t = 0`, `Nd = 0`, so the feeding coefficient is fixed exactly:
  `dNd_dt(0)/Np(0) = 683.94/10000 = 0.06839` — **not** `lambda_p = 0.1`
  (a branching/efficiency factor ≈ 0.684).
* Under a constant-rate Bateman law the implied `lambda_d = (0.0684·Np - dNd_dt)/Nd`
  would be constant. Instead it drifts smoothly from ≈0.097 (early) to ≈0.054
  (late).
* A best global linear fit `a·Np - b·Nd` leaves a **smooth, systematic**
  residual up to 30 (not random noise), and a free bi-exponential fit of `Nd`
  produces exponents 0.065 / 0.119 (not 0.05 / 0.10) with an oscillating
  residual. Prony/matrix-pencil analysis returns unstable/complex exponents.

Conclusion: `Nd(t)` is **not** a sum of a few exponentials, so the generating
right-hand side is **not** the constant-rate linear Bateman law. Three- and
four-parameter nonlinear closed forms (saturable decay, Michaelis–Menten,
`a·Np·exp(-k·Nd)`, logistic feeding, three-stage chain, …) were all tried and
none reduced the maximum error below ≈8. The kinetics contain genuine
higher-order (interaction) structure.

## 4. The adopted law

The daughter rate is well described by a **second-order kinetic law**, which we
represent as a cubic polynomial in the observed populations:

```
dNd/dt = f(Np, Nd)
       = -0.0498·Nd  + 1.020e-5·Nd²  - 2.556e-9·Nd³
         -0.1076·Np  + 4.982e-5·Np·Nd - 4.147e-9·Np·Nd²
         +2.643e-5·Np² - 4.346e-9·Np²·Nd - 8.821e-10·Np³
```

Interpretation of the leading terms:

* `-0.0498·Nd` is the daughter's radioactive decay, recovering the clean
  `lambda_d ≈ 0.05` measured independently from the tail.
* The `Np`, `Np²` and cross terms encode the parent-driven feeding of the
  daughter and its weak second-order corrections. Because `Np` carries the full
  time information, this polynomial reproduces the entire non-exponential
  `Nd(t)` shape without any explicit `t`.

### Fitting procedure

Coefficients were obtained by **tail-weighted least squares** (weight ∝ `1/Np`,
i.e. `exp(0.1 t)`). Keeping every training point prevents the polynomial from
diverging, while the weighting concentrates accuracy in the large-`t` regime
where the hidden test set lives. The Nd¹ coefficient converges to `-0.0498`,
confirming the physical `lambda_d`.

## 5. Accuracy and generalization

Reproduction on the training trajectory:

| region        | max abs err | mean abs err | mean rel err |
|---------------|-------------|--------------|--------------|
| `t ∈ [0,20)`  | 1.39 (only at `t=0`) | 0.069 | 7e-4 |
| `t ∈ [20,50)` | 0.035 | 0.014 | 2e-4 |
| `t ∈ [50,80)` | 0.009 | 0.003 | 2e-4 |
| `t ∈ [80,90)` | 0.002 | 0.001 | 3e-4 |

**Out-of-range extrapolation** (fit on `t ≤ 84`, predict `t > 84`, mimicking the
real train/test split) gives a maximum error of `~0.003` — about 0.1 % relative
error at the deepest points. The model reduces to `dNd/dt → -0.0498·Nd` as
`Np, Nd → 0`, which is the correct physical asymptotics, so it extrapolates
safely into the test tail. The worst-case error anywhere on the whole domain is
1.4 (a single point at `t=0`, 0.2 % relative), so the law is never
catastrophically wrong.

## 6. Compliance notes

* `law([row])` maps each row independently to one `{'dNd_dt': value}`.
* Uses only the declared variables (`Np`, `Nd`; `t` is accepted but redundant)
  and fixed constants inferred from training.
* No ML black box, no lookup table, no interpolation, no numerical
  differentiation, no file/hidden-data access, no cross-row state, no reliance
  on input ordering.
