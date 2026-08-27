# Discovering the law for `dv_dt`

## The physical setup

A mass on a **frictionless surface** is attached to a **hardening spring** — a
spring whose restoring force grows faster than linear at large stretch, with an
added cubic term. This is the classic **Duffing oscillator**:

$$ m\,\ddot X = -k\,X - \beta\,X^3 \quad\Rightarrow\quad \dot V = -\tfrac{k}{m}X - \tfrac{\beta}{m}X^3 $$

Released from a displacement, the mass oscillates, but — because the stiffness
depends on amplitude — the period and waveform shift with amplitude.

## What the data actually contains

Columns: `t, x, v, z, e` (inputs) and `dv_dt` (target). I probed each:

1. **`dx/dt = v` exactly** (correlation 0.99999). So `x` is a position-like
   coordinate and `v` is its velocity.
2. **`de/dt = v·z`** almost exactly (fitted coefficient 1.0005). So `e` is the
   time-integral of `v·z`.
3. **`z` and `e` are smooth functions of `(x, v)`** — polynomial fits of `z` and
   `e` in `(x, v)` reach ~1e-3 RMSE. Hence the *true dynamical state is only
   2-dimensional*, `(x, v)`; `z` and `e` are derived quantities.

### The key surprise

If `x` were the physical Duffing position, `dv_dt` would be a function of `x`
**alone**. It is not:

- A polynomial in `x` alone plateaus at RMSE ≈ 0.22 — it *cannot* fit.
- At a **fixed** `x ≈ 0.435`, `dv_dt` ranges from −0.78 (when `v ≈ 0`) to −1.40
  (when `|v|` is large). So the acceleration genuinely depends on velocity too.

This means the reported `x` is a **nonlinear transform of the underlying Duffing
position** `X` (i.e. `x = h(X)`). Differentiating twice,
`ẍ = h''(X)\,\dot X^2 + h'(X)\,\ddot X`, which injects **velocity-squared terms**
into the acceleration. Indeed, the single most important nonlinear term in every
fit is `x·v²` (coefficient ≈ −2), exactly this Jacobian signature. So in the
reported coordinates the motion obeys a second-order ODE of the form
`ẍ = f(x, ẋ)` rather than the pure `f(x)` you'd get in the natural coordinate.

## Choosing the predictive model

Since the state is `(x, v)` and `z` is a convenient smooth function of it, I fit
`dv_dt` as a **cubic polynomial in `(x, v, z)`** (20 terms, degree ≤ 3). I did
**not** simply take the lowest-error fit — I selected for **robust temporal
extrapolation**, because the hidden test set is the *later* time segment of the
same run. I retrained on the first fraction of the trajectory and measured error
on the remaining future:

| Model (features, degree)      | test@0.7 | test@0.6 | test@0.5 | test@0.4 |
|-------------------------------|---------:|---------:|---------:|---------:|
| **(x, v, z), deg 3**  ← chosen | 0.0017  | 0.0017   | 0.0101   | 0.0103   |
| (x, v), deg 4                  | 0.0099  | 0.0085   | 0.0095   | 0.103    |
| (x, v, z, e), deg 3            | 0.0020  | 0.0061   | 0.0145   | 0.0089   |
| (x, v, z, e), deg 4            | 0.0020  | 0.0049   | 0.213    | —        |

The `(x, v, z)` cubic is uniformly the most stable; adding `e` or raising the
degree overfits and blows up under extrapolation. The oscillation amplitude
**decays** over time (turning points 1.0 → 0.62 → 0.65 → 0.43 → … → 0.22), so the
future test region lives *near the origin* in `(x, v)` space — a well-sampled,
interpolated region — which is why this fit is expected to hold up.

## Final law

`dv_dt` = cubic polynomial in `(x, v, z)`:

```
dv_dt = -0.0128
        - 0.6520·x  - 0.0994·v  - 1.3586·z
        - 0.3455·x² - 0.3595·xv + 0.5969·xz - 0.0867·v² + 0.3711·vz - 0.3592·z²
        - 0.4885·x³ + 0.3598·x²v - 0.2486·x²z - 1.9612·xv² - 0.4358·xvz
        + 0.0045·xz² - 0.0062·v³ - 0.0813·v²z + 0.1896·vz² + 0.1214·z³
```

Coefficients were fit by least squares on the full training set.

**Fit quality on training data:** RMSE = 1.16 × 10⁻³, max abs error = 4.0 × 10⁻³.

The dominant terms — a large `z` coefficient (`z` acts as a second effective
position-like coordinate) and the `x·v²` Jacobian term — reflect the hardening
restoring force expressed in the (nonlinearly transformed) reported coordinates.

## Implementation

`law.py` evaluates this polynomial directly from `x`, `v`, `z` for each input row
and returns `{"dv_dt": value}`. It uses no external state and no `e`/`t`.
