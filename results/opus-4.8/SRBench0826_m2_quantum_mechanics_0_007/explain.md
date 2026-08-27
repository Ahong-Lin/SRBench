# Discovered Law: Coherent Tunneling Oscillation

## Result

The output variable is reproduced **exactly** (max absolute error ≈ 2×10⁻¹⁶,
i.e. floating-point round-off) by the closed form:

```
dPr_dt = K · N − 0.1 · Pr + 0.05
```

| term        | coefficient |
|-------------|-------------|
| `K · N`     | +1.00       |
| `Pr`        | −0.10       |
| constant    | +0.05       |

Note that the input `J` and the explicit time `t` do **not** appear — the law
is autonomous in the remaining state variables.

## How it was found

1. **Loaded and profiled the data** (`/app/data/train_data.csv`, 4500 rows).
   `dPr_dt` correlated most strongly with `K` (ρ ≈ 0.989), and a numerical
   check confirmed the `dPr_dt` column is the time derivative of `Pr`
   (`corr(np.gradient(Pr,t), dPr_dt) ≈ 1.0`).

2. **Simple linear fits were not exact.** `dPr_dt ≈ 0.836·K` left a residual
   that correlated with `Pr`, `N`, and `J`, so the relationship is a product,
   not a pure proportionality.

3. **Polynomial symbolic regression.** I built a library of all monomials up to
   degree 3 in `{Pr, J, K, N}` plus a constant and solved by least squares.
   The fit collapsed onto exactly three non-zero coefficients:

   - `K·N`  → 1.0
   - `Pr`   → −0.1
   - `1`    → 0.05

   All other candidate terms had coefficients at the 10⁻¹⁵ level (numerical
   zero). Re-evaluating the three-term formula gave machine-precision agreement.

## Physical interpretation

This is a damped two-well tunneling model expressed in Bloch-vector-like state
variables:

- `Pr` — probability of finding the particle in the initially unoccupied well.
- `K` — the tunneling-current / coherence component that drives population
  transfer between the wells. It oscillates about 0 (the sign sets the
  direction of transfer).
- `N` — a slowly decaying envelope (1 → ~0.6) that modulates the effective
  coupling; this is what makes the population oscillation *coherent but
  damped* rather than perfectly periodic. The product `K·N` is the effective
  tunneling current.

The equation

```
dPr/dt = (K·N)  −  0.1·Pr  +  0.05
```

reads as: **effective tunneling current** (`K·N`) drives the coherent
back-and-forth transfer, while a weak linear term `−0.1·Pr + 0.05` provides a
restoring/relaxation drift toward the equilibrium occupation
`Pr* = 0.05/0.1 = 0.5` (equal population of the two wells) in the absence of
current. This matches the observed behaviour: `Pr` oscillates and settles
around 0.5.

## Validity / generalization

The formula uses only the instantaneous state (`Pr`, `K`, `N`) with fixed
constants and no explicit dependence on `t`, so it extrapolates naturally to
the right-hand time segment used as the hidden test set. Because the fit is
exact on the training segment (not a statistical approximation), it should hold
on the continuation of the same experiment.

## `law.py`

`law(input_data)` takes a list of dicts with keys `t, Pr, J, K, N` and returns
a list of dicts `{"dPr_dt": ...}` computed as `K*N - 0.1*Pr + 0.05`.
