# Discovered Law for `dN_dt`

## Summary

The data come from a **seasonally-forced population model**. The instantaneous
rate of change of the total abundance `N` is a **bilinear function of the two
state variables** (`N` and the reproductive-adult abundance `R`), with
coefficients that vary **periodically in time with period P = 1** (a seasonal /
annual cycle):

```
dN/dt = b(t)·R + c(t)·N·R + a(t)·N
```

where `a(t)`, `b(t)`, `c(t)` are period-1 seasonal functions.

Interpretation of the three terms:

- `b(t)·R` — seasonal **recruitment** produced by the reproductive adults `R`
  (breeding is concentrated in part of the annual cycle).
- `a(t)·N` — seasonal **per-capita loss/growth** of the standing population.
- `c(t)·N·R` — a seasonal **density-dependent interaction** between the total
  population and the reproductive adults (a Lotka–Volterra / logistic-type
  crowding term). Its coefficient is small (`~10⁻³`) but necessary; it supplies
  the density regulation that makes the peaks and troughs of `N` saturate
  toward a carrying capacity instead of growing without bound.

Each seasonal function is written as a 6-harmonic Fourier series in the phase
`2πt`:

```
f(t) = k₀ + Σ_{h=1..6} [ kₛ,ₕ·sin(2πh·t) + k_c,ₕ·cos(2πh·t) ]
```

(the several harmonics reproduce the sharp, pulse-like breeding season rather
than a smooth sinusoid).

## Methodology

1. **Verified the target is a true derivative.** A numerical gradient of `N`
   with respect to `t` matched the supplied `dN_dt` to ~7 significant figures
   (correlation 0.99999999), confirming `dN_dt = dN/dt` for a genuine ODE.

2. **Ruled out an autonomous `f(N,R)` law.** A nearest-neighbour test found
   rows with essentially identical `(N, R)` (e.g. `N≈216.5, R≈145.9`) but very
   different targets (`dN_dt ≈ +123` vs `−32`). These rows differ in `t` by a
   fraction of a period, proving the right-hand side depends on time (phase)
   explicitly — the system is periodically forced. Polynomial fits in `(N,R)`
   alone plateaued at R² ≈ 0.28.

3. **Found the period.** Successive maxima of `N` occur at
   t ≈ 0.42, 1.38, 2.38, 3.37, 4.37, 5.36, 6.36 — spacing converging to
   **1.00**. Optimising the period against held-out extrapolation error also
   selected P = 1.000. Angular frequency `ω = 2π` is used throughout.

4. **Identified the term structure.** Starting from a mechanistic
   `dN/dt = R·b(t) − d·N` (which already gave the correct period 1.000),
   forward selection of seasonal terms showed that the triple
   `{N, R, N·R}` with seasonal coefficients captures the dynamics; adding
   `N²` or `R²` gave no improvement. This is the reported bilinear form.

5. **Chose harmonic order by honest extrapolation.** Models were fit on the
   early time segment (first 60–80% of `t`) and scored on the **late** segment
   to mimic the hidden right-hand test. The `{N, R, N·R}` seasonal structure
   extrapolates cleanly, with no train/test gap:

   | harmonics | train R² | late-segment (extrapolation) R² |
   |-----------|----------|---------------------------------|
   | 4         | 0.9986   | 0.9987 |
   | 6         | 0.99997  | 0.99987 |
   | 8         | 0.99999  | 0.99989 |

   Training on only the first 60% and predicting the last 40% still gives
   R² = 0.9997. **6 harmonics** were selected as the balance of accuracy and
   parsimony.

6. **Final fit.** Coefficients were re-estimated by ordinary least squares on
   the full training set (linear in all coefficients, given P = 1). Full-data
   R² = **0.99997**.

## Fitted parameters

Period `P = 1` (`ω = 2π`), 6 harmonics per seasonal function. Fourier
coefficients are stored in `law.py` as `_C_R` (for `b(t)`, the `R` term),
`_C_RN` (for `c(t)`, the `N·R` term) and `_C_N` (for `a(t)`, the `N` term), each
ordered `[const, sin₁, cos₁, …, sin₆, cos₆]`.

Leading (annual-mean) values give the qualitative balance:
`b̄ ≈ 1.77` (mean recruitment per adult), `ā ≈ −0.76` (mean per-capita loss),
`c̄ ≈ −2.9×10⁻³` (mean density-dependent drag).

## The `law` function

`law(input_data)` maps each row independently to its prediction:

```
dN_dt = b(t)·R + c(t)·N·R + a(t)·N
```

using only the declared variables `t`, `N`, `reproductive_adult_abundance` and
the fixed constants above. It carries no state between calls, does no
interpolation or data access, and is a fully explicit pointwise function, valid
for `t` beyond the observed window because the seasonal forcing is strictly
periodic with period 1.
