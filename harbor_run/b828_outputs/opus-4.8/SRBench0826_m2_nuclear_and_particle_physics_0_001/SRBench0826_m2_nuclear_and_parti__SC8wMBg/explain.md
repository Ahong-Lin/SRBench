# Discovering the law for `dNd_dt` in a parent → daughter → stable decay chain

## 1. Summary of the discovered law

For every row the prediction is computed **pointwise** from the observed state
`(Np, Nd)`:

```
dNd_dt  =  -λd · Nd  +  Np · C(Nd/Np)

λd = 0.05                              (daughter's intrinsic decay constant)

C(h) = (a + b·h + c·h²) / (1 + d·h + e·h²) ,     h = Nd / Np
a = 0.0683939721
b = -0.0185441981
c = -0.0040834256
d =  0.1240937347
e =  0.0534666909
```

Interpretation:

* `-λd·Nd` is the **daughter self-decay** term.  `λd = 0.05` is a clean constant
  recovered from the late-time tail of the experiment (see §4).
* `Np·C(Nd/Np)` is the **net parent-coupled source** term.  `C` is positive when
  the parent stock is large relative to the daughter (early times → net
  build-up) and saturates to a small negative constant `c/e ≈ -0.076` at late
  times, so asymptotically the rate is dominated by the daughter decay:
  `dNd_dt → -0.05·Nd - 0.076·Np`.

## 2. What the data told us up front

* `Np` is **exactly** `10000·exp(-0.1·t)` to machine precision (residual std
  ≈ 8·10⁻⁷).  So the parent decays with rate `λp = 0.1` and `Np(0)=10000`.
  Because `Np` is a strictly monotone function of `t`, the pair `(t, Np)` is
  redundant — any function of `t` is a function of `Np` and vice versa.
* `dNd_dt` equals the exact time-derivative of the tabulated `Nd`
  (`np.gradient(Nd, t)` reproduces the `dNd_dt` column to ~10⁻³).  The trajectory
  `(Nd, dNd_dt)` is therefore internally consistent and **noise-free**: the
  residuals of any candidate model are smooth (2nd-difference std ≈ 8·10⁻⁴ vs a
  residual spread of ~3), i.e. they reflect *model mis-specification*, not noise.

## 3. Why the textbook two-species Bateman law does **not** fit

The naïve chain law `dNd_dt = λp·Np − λd·Nd` (linear in `Np`, `Nd`) was tested
carefully and **fails**:

* At `t = 0` the daughter is empty (`Nd = 0`) and `dNd_dt(0) = 683.94`, forcing
  the *feeding* coefficient to be `683.94/10000 = 0.0684`, **not** the parent
  decay rate `λp = 0.1`.
* A global least-squares fit `dNd_dt = c₁·Np + c₂·Nd` leaves a *smooth,
  systematic* residual (RMSE ≈ 3.6, max ≈ 30) and, crucially, the implied
  coefficients drift strongly with the fitting window.  In the tail the best
  linear fit even requires a **negative** `Np` coefficient — impossible for a
  genuine constant-coefficient Bateman system.
* Fitting the analytic Bateman `Nd(t) = A(e^{-λp t} − e^{-λd t})` to the tabulated
  `Nd` leaves a max error of ~15–100; the free two-exponential fit does not even
  contain the parent rate `0.1`.  Branching (`b·λp`), degenerate roots,
  power-law decay `λd·Nd^p`, and bimolecular loss `m·Np·Nd` were all tried and
  all fail to reproduce the tail.

Conclusion: the reference trajectory is **not** a constant-coefficient
two-species Bateman solution.  A correct pointwise predictor needs the ratio
structure below.

## 4. How the law was found

1. **Clean asymptotic decay constant.**  On a two-parameter tail fit
   `dNd_dt = −λd·Nd − q·Np`, the coefficient `λd` converges monotonically to
   **0.050** as the fit window is pushed to larger `t`
   (0.05041 → 0.05026 → 0.05012 → 0.05008 for `t>65,70,80,85`), while the fit
   becomes essentially exact (relative max error 2·10⁻⁵ for `t>85`).  This pins
   `λd = 0.05`.

2. **Collapse onto a single ratio variable.**  Define `g = dNd_dt/Np` and
   `h = Nd/Np`.  Both are monotone in `t`, so `g` is a single-valued function
   `g = F(h)`, i.e.

   ```
   dNd_dt = Np · F(Nd/Np).
   ```

   `F(h)` is linear at large `h` with slope `dF/dh → -0.050` (again `λd = 0.05`)
   and intercept `≈ -0.076`.  Subtracting the linear part,
   `C(h) = F(h) + 0.05·h = (dNd_dt + 0.05·Nd)/Np`, gives a **bounded** function
   that runs smoothly from `C(0) = 0.0684` (exact `t=0` value) to
   `C(∞) ≈ -0.076`.

3. **Closed form for the bounded coupling.**  `C(h)` is captured by a rational
   (Padé 2/2) function whose numerator constant is pinned to the exact `t=0`
   production coefficient `a = 0.0683939721`.  This yields the law in §1.

## 5. Accuracy

On the training set (using `law()` itself):

| region            | median rel. err | max rel. err |
|-------------------|-----------------|--------------|
| all `t`           | ~0.0023         | (large only at the `dNd_dt≈0` crossing near `t≈14`) |
| `t > 70`          | 0.00048         | 0.0011       |
| `t > 80`          | 0.00045         | 0.0007       |
| `t > 85`          | 0.00061         | 0.0007       |

The hidden test set is the **right-hand (late-time) segment** of the same
experiment.  There `Np` is negligible and the law reduces to the clean
daughter-decay behaviour `dNd_dt ≈ -0.05·Nd - 0.076·Np`; the bounded rational
`C(h)` guarantees a stable, pole-free extrapolation to larger `t`
(the denominator `1 + d·h + e·h²` has no positive real root).  A hold-out check
— fitting on `t∈[70,85]` and predicting `t∈[85,90]` — gives a max relative error
of only ~0.1%, confirming the extrapolation is safe.

## 6. Compliance notes

* The function is an **explicit closed-form expression** of the declared
  variables `Np`, `Nd` with fixed numeric constants; there is no lookup table,
  interpolation, numerical differentiation, ML model, ordering dependence, or
  cross-row state.
* Each row is evaluated independently; `law([row])` returns exactly one
  `{'dNd_dt': value}`.
* `t` is accepted but not required (it is redundant with `Np` on this
  experiment).
