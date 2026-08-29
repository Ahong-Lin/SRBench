# Discovering the law for `dvx_dt`

## Summary

The data describes a small body on a **bound, precessing orbit**. The dominant
force is Newtonian inverse-square gravity toward a fixed center at the origin,
but the orbit is **not** a pure Kepler ellipse: it precesses and its angular
momentum about the origin is not conserved. The instantaneous right-hand side is

```
dvx_dt = -GM · x/r³  +  A · x/r⁵  +  B · x·(x² − y²)/r⁷  +  C · vx/r²
         └──monopole──┘  └────── quadrupole + extra radial ──────┘  └─ drag ─┘
```

with `r = √(x² + y²)` and constants fitted from the training set:

| constant | value        | meaning |
|----------|--------------|---------|
| `GM`     | `0.99940167` | gravitational monopole `G·M` (≈ 1) |
| `A`      | `0.06480147` | coeff. of `x/r⁵` (= 0.05 quadrupole + 0.01494 extra radial 1/r⁴) |
| `B`      | `-0.12501777`| coeff. of `x(x²−y²)/r⁷` (≈ `−1/8` = `5·Q`, `Q = −1/40`) |
| `C`      | `-0.00379919`| coeff. of `vx/r²` (small velocity-dependent term) |

**Fit quality:** `R² = 0.99999973`, RMSE `≈ 1.0×10⁻³`, max abs error `≈ 2.8×10⁻³`
over the full training set, and it **generalizes to the held-out right-hand time
segment with the same accuracy** (train on first 70 %, evaluate on last 15 %:
RMSE `1.2×10⁻³`, max `2.2×10⁻³`).

## How the law was discovered

### 1. State consistency
First I confirmed the data is a clean, self-consistent trajectory:
`vx = dx/dt`, `vy = dy/dt`, and `dvx_dt = d(vx)/dt` all hold to `≈10⁻⁵–10⁻⁶`
(high-order finite differences on the uniform time grid, `Δt ≈ 2×10⁻³`).
So `dvx_dt` is a precise pointwise function of the state, not noise.

### 2. Pure Kepler fails
The naive law `dvx_dt = -GM·x/r³` gives a *terrible* fit (RMSE ≈ 0.48, max
error ≈ 1.9, i.e. > 100 %). The ratio `dvx_dt / (-x/r³)`, which should equal a
constant `GM`, instead varies from ~0.67 to ~1.05. Something beyond a monopole
is present.

### 3. The force is not central about the origin
Reconstructing the full acceleration vector (`ax = dvx_dt` exact, `ay` from a
5-point finite difference of `vy`), the torque about the origin
`τ = x·ay − y·ax = dL/dt` is **not zero** — angular momentum oscillates by ~5 %.
Crucially, `τ` correlates with `x·y/r⁵` at **−0.9997**. Since
`x·y/r⁵ = sin(2θ)/(2r³)`, this is the unmistakable signature of a **quadrupole
(m = 2, `cos 2θ`) potential**.

### 4. Isolating the quadrupole
Decomposing the perturbing acceleration into polar components gives an
extremely clean **tangential** part:

```
a_t = β · sin(2θ) / r⁴      (correlation −1.0000, radial exponent = 4.004)
```

For a conservative force `a_t = −(1/r)∂U/∂θ`, this integrates to the potential

```
U_quad = Q · (x² − y²) / r⁵ = Q · cos(2θ) / r³ ,   Q = −1/40 ,
```

whose x-force is `−2Q·x/r⁵ + 5Q·x(x²−y²)/r⁷ = 0.05·x/r⁵ − 0.125·x(x²−y²)/r⁷`.
The `x(x²−y²)/r⁷` coefficient comes out to `B ≈ −0.125 = −1/8` exactly.

### 5. Two small residual terms
After removing the monopole and quadrupole, a residual of RMSE ≈ 0.11 remains:

* It correlates ~0.99 with `x/r⁵`, i.e. an **extra central force ∝ 1/r⁴**
  (coefficient ≈ 0.0149). This is what makes the free-fit `x/r⁵` coefficient
  `A = 0.05 + 0.0149 = 0.0649` instead of the pure-quadrupole 0.05.
* A further residual (RMSE ≈ 0.001) correlates ~0.95 with **`vx/r²`**, a small
  **velocity-dependent (drag-like) force ∝ v/r²** (coefficient `C ≈ −0.0038`).
  This is a genuine velocity dependence: no purely positional model — I tested a
  75-term multipole library — can remove the `vx` correlation, and adding
  `vx/r²` improves the held-out RMSE ~10× (0.011 → 0.001). Note only the
  x-component (`vx/r²`) enters `dvx_dt`; the `vy/r²` term correctly does not help.

### 6. Convergence check
Adding higher multipoles (`cos 4θ`, `1/r⁹` terms) or other velocity powers
yields no meaningful improvement — the held-out error plateaus at ~10⁻³. The
four-term law above is therefore the parsimonious, well-generalizing description.

## Physical interpretation

The system is a **perturbed Kepler orbit**:

* **Monopole** `−GM·x/r³` — inverse-square gravity toward the heavy central body
  (`GM ≈ 1`), the dominant term.
* **Quadrupole** `U_q = −(1/40)(x²−y²)/r⁵` — a non-spherical (bar-/J2-like)
  component of the central mass distribution. It breaks the `1/r` symmetry,
  drives the observed **apsidal precession**, and exchanges angular momentum
  with the orbit (torque `∝ sin 2θ`).
* **Extra `1/r⁴` central force** — a smaller short-range central correction.
* **`v/r²` drag-like term** — a weak velocity-dependent force.

## Constraints honored

`law(input_data)` maps each row independently using only the declared variables
`x, y, vx, vy` and fixed fitted constants (`t` is not needed). There is no
machine-learning model, lookup table, interpolation, numerical differentiation,
file access, cross-row state, or dependence on input ordering. Each call returns
a list with exactly one dict `{'dvx_dt': value}`. (Finite differences were used
**only offline** to analyze the data and discover the closed form; they are not
part of the submitted `law`.)
