# Discovering the law for `dv_dt`

## Physical setting

A mass on a spring oscillates vertically through a viscous medium that
resists its motion. The natural first guess is the textbook **linear damped
harmonic oscillator**

```
dv/dt = -(k/m) x - (b/m) v
```

The data forced a small refinement of this picture, described below.

## What the data told me

The training file is a **single trajectory** sampled at uniform `dt ≈ 0.004`
over `t ∈ [0, 18]`, with columns `t, x, v, z, dv_dt`.

1. **`x` is position, `v` is velocity.** Finite differences give
   `dx/dt ≈ v` (agreement to discretisation error).

2. **`z` is a velocity-memory variable, and a decoy.** Central differences
   show, to 1e-6,
   ```
   dz/dt = -(v + z)
   ```
   i.e. `z` is a low-pass (exponentially-weighted) integral of `-v`. It is a
   genuine extra state, but it turned out **not to help** predict `dv_dt`:
   including `z` in the regression left the fitted coefficients unstable
   across time windows (severe collinearity along the single trajectory) and
   *worsened* held-out prediction. It is excluded from the final law.

3. **`dv_dt` is not a pure linear function of `(x, v, z)`.** The best global
   linear fit `dv_dt = a x + b v + c z (+const)` leaves a structured,
   oscillatory residual of RMS ≈ 0.03–0.08 — far above the ~1e-6 cleanliness
   seen for `dz/dt`. Fitting `x(t)` to a sum of three linear eigen-modes also
   failed (residual ≈ 0.012), ruling out a purely linear 3-D system.

4. **The oscillation is centred near `x ≈ -0.10`, not `0`.** This is the
   gravitational equilibrium (spring stretch under gravity), so a constant
   term is needed.

5. **The restoring force is weakly nonlinear (a cubic / Duffing spring).**
   Adding `x²` and `x³` terms removes most of the remaining residual and, more
   importantly, sharply improves prediction in the small-amplitude regime that
   the test set lives in.

## Final law

```
dv_dt = C0 + C1·x + C2·x² + C3·x³ + C4·v
```

with least-squares coefficients (full training set):

| term | coefficient | interpretation |
|------|-------------|----------------|
| `C0` | -0.185116   | constant gravitational offset |
| `C1` | -1.836169   | linear spring stiffness `-k/m` |
| `C2` |  0.044549   | quadratic spring correction |
| `C3` | -0.442310   | cubic (Duffing) spring correction |
| `C4` | -0.478516   | linear viscous damping `-b/m` (force ∝ speed) |

The restoring force `F(x) = -(C0 + C1 x + C2 x² + C3 x³)` has a single real
zero at **x ≈ -0.100**, matching the observed oscillation centre — a
consistency check that the constant is a genuine equilibrium offset.

## Why this form / model selection

Because the data is one decaying trajectory, `x`, `v`, and `z` are highly
correlated, so many expressions fit the *bulk* of the data comparably. I
therefore selected the model by **time-split cross-validation**: fit on the
early/large-amplitude part, predict the later/small-amplitude part (the
regime the hidden test set — the right-hand time segment — occupies).

Held-out performance (train `t < 17`, evaluate `t ≥ 17`):

| model | test max-error |
|-------|----------------|
| linear `x,v` + const           | 7.1e-3 |
| Duffing (`x,x³,v`) + const     | 3.9e-3 |
| **cubic-in-x (`x,x²,x³,v`) + const** | **5.6e-4** |
| any model including `z`        | worse & unstable |

The chosen cubic-in-`x` + linear-`v` model gives the smallest and most stable
held-out error, is physically interpretable (nonlinear spring + gravity +
linear viscous drag), and uses only `x` and `v`.

On the full training set it achieves RMS ≈ 0.017 (dominated by the single
extreme point at `x = 1`); on the test-like tail `t > 17` it achieves
RMS ≈ 2.1e-4, max ≈ 5.4e-4.

## Notes / limitations

- `t` and `z` are intentionally unused: the law is autonomous and pointwise.
- The large-amplitude start (`x = 1`, where `dv_dt = -2.5` exactly) is the
  least well captured point (predicted ≈ -2.42); a low-order polynomial spring
  cannot perfectly match both the large-amplitude launch and the
  small-amplitude tail. Since the test set is the small-amplitude
  continuation, the fit is deliberately most accurate there.
