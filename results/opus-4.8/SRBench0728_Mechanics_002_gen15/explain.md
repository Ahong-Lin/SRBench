# Discovering the law for `dvx_dt`

## 1. What the data is

The dataset is a single, densely-sampled trajectory (`dt ≈ 0.01`, `t ∈ [0, 45]`) of a
2‑D dynamical system with state `(x, y, vx, vy)`. I verified it is a genuine, self-consistent
ODE integration:

- `d/dt x ≈ vx` and `d/dt y ≈ vy` (numerical derivatives match to ~1e‑3),
- the numerical derivative of `vx` matches the supplied `dvx_dt` to ~6e‑4.

So `dvx_dt` is the true x‑acceleration `a_x(x, y, vx, vy)` of an autonomous system.

## 2. Qualitative behaviour

The particle starts at `(x,y)=(4,0)`, `(vx,vy)=(0,1)` and **spirals inward**, its speed
dropping from `|v|=1.0` toward `≈0.64` and its radius from `r=4.0` toward `r≈1.45`. By
`t≈15` it is on a nearly-circular, very slowly shrinking orbit — a **stable attractor /
limit cycle**. Decomposing the acceleration into components along and perpendicular to the
velocity shows:

- On the attractor the along-velocity acceleration (`dv/dt`) is ≈ 0 — no net dissipation.
- The along-velocity dissipation coefficient `λ ≡ -a_∥/|v|` is ≈ 0 near `r≈1.47` and grows
  with `r` (≈0.15 at `r≈3.2`). This is a **van der Pol / Rayleigh-type damping**: energy is
  removed at large `r` and the system relaxes onto the limit cycle.
- The acceleration has a strong component proportional to `vy` (velocity-perpendicular /
  rotational, magnetic-Coriolis-like) plus a central `1/r²`-type attraction.

Because the orbit is still *slowly* contracting at the end of the training window
(`r: 1.494 → 1.460` over `t: 15 → 45`), the hidden right-hand segment lies on the same
attractor but at slightly smaller radius. The law must therefore be accurate over the whole
observed range of `r` (≈1.46–4.0), not just memorize one circle.

## 3. The fitted law

Combining the identified ingredients (central attraction, a rotational `vy` term, and
`r²`-scaled + speed-scaled velocity damping), the model is linear in these physically
motivated features:

```
dvx_dt =  c_vy · vy
        + c_g  · x/r³   + c_gy · y/r³        (central-force components)
        + c_dx · r²·vx  + c_dy · r²·vy       (van der Pol radial damping, ∝ r²·v)
        + c_vx · vx     + c_v2vy · |v|²·vy   (linear + cubic velocity terms)
        + c_x  · x      + const
```

with `r = √(x²+y²)`, `|v|² = vx²+vy²`.

Fitted coefficients (least squares on the full trajectory):

| term        | coefficient |
|-------------|-------------|
| `vy`        |  0.474190 |
| `x/r³`      | -0.333746 |
| `y/r³`      | -1.059213 |
| `r²·vx`     |  0.044379 |
| `r²·vy`     |  0.063090 |
| `vx`        | -0.868467 |
| `|v|²·vy`   | -1.384429 |
| `x`         | -0.105669 |
| const       |  0.000616 |

## 4. Methodology

1. **Consistency check** — confirmed `(x,y,vx,vy,dvx_dt)` form one integrated trajectory.
2. **Vector-field analysis** — reconstructed `a_y` numerically and decomposed the
   acceleration into radial/tangential and parallel/perpendicular-to-velocity components.
   This revealed (i) a velocity-perpendicular (rotational) term, (ii) a central attraction,
   and (iii) an `r`-dependent damping that vanishes on the limit cycle.
3. **Feature construction & selection** — built a library of physically-motivated features
   (central `x/rᵖ`, rotational `vy`, van der Pol `r²·v`, drag `vx`, `|v|²·v`) and selected a
   compact subset by **time-split validation**: fit on the early portion, validate on the
   latest / innermost portion (`t>40`), which is the best available proxy for the hidden
   right-hand extrapolation segment.
4. **Model choice** — the chosen 8-term model gave the best held-out extrapolation
   (validation R² = 0.9987 on `t>40`), beating both a minimal 2-term model and a larger
   "kitchen-sink" polynomial (which overfit and generalized worse).

## 5. Performance

Refit on the full trajectory, the model achieves:

- Whole trajectory: R² = 0.982 (the hard part is the fast initial transient at large `r`).
- Settled region `t>15` (what the hidden test extends): **R² = 0.99991, RMSE ≈ 0.0018**.
- Innermost region `t>40` (closest to the test): **R² = 0.99941, RMSE ≈ 0.0026**.

All features are bounded on the attractor, so the model behaves smoothly as the orbit
continues its slow contraction beyond the observed window.

## 6. Notes / caveats

- The `x/r³` and `y/r³` pair, together with the `vy` term, together represent the
  combined central + rotational forcing; the individual coefficients are somewhat
  correlated on the thin settled manifold, but the *combination* is well constrained and
  validated out-of-sample.
- The `r²·vx`, `r²·vy` and `|v|²·vy` terms encode the amplitude-dependent (van der Pol-type)
  damping that produces the stable limit cycle and the slow inward drift.
