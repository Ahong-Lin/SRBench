# Discovering the law for `dv_dt`

## 1. Problem framing

The dataset comes from a mass on a (nominally frictionless) surface attached to
a spring with a **cubic hardening** restoring force — a Duffing-type oscillator.
We must predict the instantaneous acceleration `dv_dt` as an explicit, pointwise
function of the observed variables `t, x, v, z, e`.

## 2. What the variables are

Numerical checks on the training trajectory (uniform time step `dt ≈ 0.004`):

| Relation checked (finite differences) | Result |
|---|---|
| `d/dt(x)` vs `v` | correlation `0.99999999` → **`x` is position, `v` is its velocity** |
| `d/dt(v)` vs `dv_dt` column | correlation `0.99999999` → **`dv_dt` is the true acceleration `a = v̇`** |

So `(x, v)` is a genuine kinematic pair and `dv_dt` is the acceleration we model.

`z` and `e` are **auxiliary recorded signals**, not independent inputs:

* Fitting `z = f(x, v)` and `e = f(x, v)` with a polynomial basis gives `R² ≈ 0.999`
  (residual shrinks as the basis grows), so both essentially live on the
  `(x, v)` state manifold.
* `z` behaves like a **lagged/filtered position**: early on `z ≈ x − 1` (and the
  tiny gap equals `e` to machine precision), but the two drift apart later, so
  `z` carries a *small* amount of extra dynamical information beyond `(x, v)`.
* `e` is an **energy-like** signal (always ≥ 0, rising from 0 to a ~0.64 plateau
  as the oscillation settles); it is not needed once `x, v, z` are used.

## 3. Why the naive Duffing law fails

The textbook law `dv_dt = −(k/m)·x − (β/m)·x³` is a function of `x` **only**. The
data rules this out:

* At `x ≈ −0.10` the acceleration takes values from `+0.2` up to `+1.5`
  depending on the velocity — a single-valued `f(x)` cannot do this.
* The acceleration is **large when `|v|` is large** (e.g. `x≈−0.10, v≈−1.38 →
  dv_dt≈+1.46`). In pure SHM the acceleration is ~0 at maximum speed; here it is
  the opposite, exposing a strong **velocity coupling**.
* Energy is **not** conserved: at the same `x`, `v²` differs (e.g. `1.90` vs
  `1.21`). Successive turning-point amplitudes decay (`1.00 → 0.62 → 0.43 → …`),
  so the motion is **damped / amplitude-dependent**, not a clean conservative
  Duffing.

A least-squares `dv_dt = a·x + b·x³` therefore has max error `> 1.3`.

## 4. The relationship that works

The acceleration is a smooth (analytic) function of the observed state. A
**bivariate Taylor expansion in `(x, v)`** captures it, and a single extra
**linear `z`** term captures the residual dynamical information:

```
dv_dt = P(x, v) + c_z · z ,     P = Σ  c_ij · x^i · v^j   (all i + j ≤ 4)
```

Fitting by ordinary least squares on the full training set. The dominant terms
are physically interpretable:

| term | coefficient | reading |
|---|---:|---|
| `x · v²` | −1.996 | velocity-dependent (geometric / kinematic) coupling |
| `z`      | −1.281 | restoring contribution carried by the lagged state |
| `x`      | −0.728 | linear restoring stiffness (shared with the `z` term) |
| `x³`     | −0.514 | **cubic hardening** of the spring |
| `x⁴`     | −0.194 | higher-order correction |
| `x² v²`  | −0.168 | mixed correction |
| smaller `v, v², v³, x², …` | — | remaining Taylor corrections / light damping |

(The `x` and `z` restoring terms share the load because `z ≈ x`; together they
supply the effective linear stiffness.)

## 5. Accuracy and validation

Fit on the **full** training set:

* max abs error = **0.0055**
* RMSE = **0.0020**  (target range ≈ ±1.8)

**Generalization to the right-hand time segment** (the held-out test is a later,
smaller-amplitude continuation). Training on the earlier part and validating on
the later part:

| model | train 60% → val last 40% (max err) | train 50% → val last 50% |
|---|---:|---:|
| deg-4 `P(x,v)` | 0.0155 | 0.0209 |
| deg-4 `P(x,v) + z` (**used**) | **0.0082** | 0.008 |
| deg-6 `P(x,v)` | 0.0335 | 0.1016 (overfits) |

Degree 4 is the sweet spot: higher degrees fit the training data better but
**extrapolate worse** to the later, lower-amplitude regime. Adding the single
linear `z` term roughly halves the validation error, so it is retained.

## 6. Implementation notes (`law.py`)

* `law` maps **each row independently** to one `{"dv_dt": …}` value.
* It uses only the declared variables `x, v, z` (with `t`, `e` unused) and fixed
  constants inferred from training.
* No ML black box, no lookup/interpolation, no numerical differentiation, no
  data reads, no cross-row state — a plain closed-form polynomial evaluation.

## 7. Honest caveats

The clean two-parameter Duffing form does not describe this dataset; the data
show genuine velocity coupling and amplitude decay. The presented law is the
most accurate **interpretable, well-extrapolating** closed form found — a
degree-4 polynomial in `(x, v)` plus a linear `z` term, which we read as a
damped, hardening, amplitude-dependent oscillator. The largest single physical
signatures are the cubic hardening (`x³`) and the `x·v²` velocity coupling.
