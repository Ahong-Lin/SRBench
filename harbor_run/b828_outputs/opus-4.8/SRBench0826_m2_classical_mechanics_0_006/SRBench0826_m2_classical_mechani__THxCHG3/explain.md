# Discovering the law for `dvx_dt`

## Summary

The data is **not** a pure Kepler two‑body orbit. It is a small body orbiting a
central body whose gravitational potential has a **quadrupole (l = 2) moment**, plus a
**weak drag** that slowly removes orbital energy. The discovered right‑hand side is

```
r = sqrt(x^2 + y^2)

dvx_dt = -GM · x/r^3                    (Newtonian monopole gravity)
         + a2 · x/r^5                   (axisymmetric part of the quadrupole)
         + a3 · x·(x^2 - y^2)/r^7       (cos 2θ part of the quadrupole)
         - k  · vx/r^2                  (weak drag ∝ v / r^2)
```

with constants fit to the training data:

| constant | value | meaning |
|---|---|---|
| `-GM` | `-0.99940` | Newtonian monopole, so `GM ≈ 1.0` |
| `a2`  | `+0.06480` | `= 3C − 2B` (radial quadrupole coefficient) |
| `a3`  | `-0.12502` | `= 5B`, giving `B ≈ -0.025` |
| `-k`  | `-0.00380` | drag strength, `k ≈ 0.0038` |

On the full training set this gives **RMS ≈ 1.0×10⁻³**, **max abs error ≈ 2.8×10⁻³**,
**R² ≈ 0.9999997**. Trained on `t < 5.5` and evaluated on `t ≥ 5.5` (the same kind of
left/right time split as the hidden test), the test RMS is ≈ 1.2×10⁻³ with essentially
unchanged coefficients — the law extrapolates in time.

## How I found it

The columns are internally consistent: `dvx_dt` matches a finite difference of `vx`
to ~10⁻⁶, and `vx = dx/dt`. So the data is a genuine, smoothly integrated trajectory,
and the task is to identify the force field that produced it.

**1. Pure Kepler fails.** Fitting `dvx_dt = -GM·x/r³` leaves an RMS of ~0.48
(≈25 % of the signal). Integrating a Kepler orbit from the initial conditions does not
reproduce the recorded path. So there is a real perturbation.

**2. The force is (almost) a function of position only.** Points where the orbit
revisits the same `(x, y)` at very different times/velocities have nearly identical
`dvx_dt`. This rules out any explicit time dependence (a moving/rotating center) and
shows the dominant force is a static field.

**3. It is not a single central force.** The angular momentum `L = x·vy − y·vx`
is **not conserved** (it oscillates by ~5 %), and no offset center conserves it.
Reconstructing the full acceleration vector `(ax, ay)` (with `ax` exact and `ay` from a
4th‑order finite difference of `vy`, accurate to ~10⁻⁶) and decomposing into radial and
tangential parts revealed a clear **tangential acceleration**:

```
a_t ∝ sin(2θ) / r^4     (log–log fit gives the exponent −4.00)
```

A `sin 2θ` tangential force is the signature of an **l = 2 quadrupole / bar** term in
the potential. The matching radial piece goes as `cos(2θ)/r^4`. Together these are the
gradient of

```
U_quad = (C + B·cos 2θ) / r^3 = C/r^3 + B·(x^2 - y^2)/r^5 .
```

Its Cartesian x‑gradient produces exactly the `x/r^5` and `x·(x²−y²)/r^7` terms. The
`x·(x²−y²)/r^7` coefficient is `5B` and comes out to `B ≈ −0.025` **consistently in both
the `ax` and `ay` fits**, confirming a single physical quadrupole moment.

**4. A weak drag completes the model.** After removing the quadrupole, the residual
(~10⁻²) still could not be reduced by any richer *position‑only* basis (it floored at
~7.6×10⁻³), but it correlated strongly with `vx/r²`. Adding a term `−k·vx/r²` dropped the
RMS by an order of magnitude to ~10⁻³. The **same** term appears symmetrically in `ay`
as `−k·vy/r²` with the same `k ≈ 0.0038`, i.e. an isotropic drag `−k·v/r²`. This drag is
strongest near perihelion, removes energy, and explains the observed slow decay of the
perihelion distance (0.470 → 0.450 → 0.424 over the three recorded passages) and the
non‑conservation of energy and angular momentum.

**5. Rejected alternatives.**
- *Softening / different power law* `-GM·x/(r²+ε²)^{3/2}` or `x/r^p`: cannot match both
  the aphelion (`GM≈1.06` at r=1) and perihelion behavior simultaneously.
- *Offset / moving / rotating center* and *restricted 3‑body (CR3BP)*: fitted rotation
  rate ≈ 0 and residual ~0.10; no rotating frame conserves a Jacobi‑type integral here.
- *Two fixed point masses*: fits to ~0.10 but does not reach machine precision and is not
  the true generator.
- *Post‑Newtonian (Einstein–Infeld–Hoffmann) velocity terms* `v²x/r³`, `(r·v)vx/r³`:
  ill‑conditioned and left RMS ~0.21; the perturbation is a static quadrupole, not PN.

## The law used

Only `x`, `y`, `vx` enter the `x`-component (as required, `vy` and `t` are not needed):

```
dvx_dt = -0.99940·x/r³ + 0.06480·x/r⁵ − 0.12502·x·(x²−y²)/r⁷ − 0.00380·vx/r²
```

Each input row is mapped independently; there is no state between calls, no data
access, no interpolation, and no ordering dependence. `r ∈ [0.42, 1.0]` on the orbit, so
the `1/rⁿ` factors are always well defined.
