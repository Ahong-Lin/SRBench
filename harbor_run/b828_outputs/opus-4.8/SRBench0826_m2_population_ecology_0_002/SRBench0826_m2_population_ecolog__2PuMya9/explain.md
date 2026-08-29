# Discovered law: prey dynamics in a predator–prey reserve

## Result

The instantaneous prey growth rate is governed by the **Rosenzweig–MacArthur
model** — logistic prey growth minus predation with a Holling type II
(saturating) functional response:

```
dN/dt = r · N · (1 − N/K)  −  a · N · P / (1 + b · N)
```

with fitted constants

| symbol | meaning                              | value      |
|--------|--------------------------------------|------------|
| `r`    | intrinsic prey growth rate           | 0.79803    |
| `K`    | prey carrying capacity               | 99.908     |
| `a`    | predator attack (search) rate        | 0.13054    |
| `b`    | handling / saturation coefficient    | 0.021947   |

## How it was found

1. **Framing.** The target `dN_dt` is the right-hand side of the prey ODE. I
   worked with the per-capita growth rate `g = dN_dt / N`, which for any
   logistic-type prey equation is linear in the self-limitation and predation
   terms.

2. **Structure discovery.** Regressing `g` against candidate terms showed it is
   dominated by predator abundance `P` (corr ≈ −0.92) plus a linear `N`
   self-limitation term (`g ≈ r − (r/K)·N − a·P`, R² ≈ 0.94). The remaining
   curvature was captured by an `N·P` interaction, the signature of a
   **saturating (Holling II) predation response** rather than a bilinear
   Lotka–Volterra term.

3. **Nonlinear fit.** Fitting the full Rosenzweig–MacArthur form by nonlinear
   least squares gave an excellent, tight fit:
   - **R² = 0.99984** on the full training set (residual σ ≈ 0.057 vs. output σ ≈ 4.57).
   - **R² = 0.999** on a held-out right-hand time segment (last 20 %), i.e. the
     same regime as the hidden test set — so the law generalizes, it is not
     overfit.
   - Parameter standard errors are ~0.02–0.4 % of the estimates.

   A plain Lotka–Volterra with logistic prey (`−a·N·P`, no saturation) only
   reaches R² ≈ 0.83, confirming the saturating functional response is real.

## Interpretation

- `r·N·(1 − N/K)`: prey reproduce in the predator's absence, self-limited near
  carrying capacity `K ≈ 100` (matching the observed prey ceiling).
- `a·N·P/(1 + b·N)`: predation is proportional to encounters (`N·P`) but
  saturates at high prey density because predators need handling time. The
  half-saturation prey density is `1/b ≈ 46`; the maximum per-predator intake is
  `a/b ≈ 6`.
- This structure produces the recurring boom-and-bust limit cycles described in
  the experiment.

## On the `R` column

`R` co-varies with the prey abundance and with the functional-response term
(corr ≈ 0.89 with `a·N/(1+b·N)`) but is a **separate dynamic variable** of the
system, not needed to predict `dN_dt`. Adding an `R` term to the fitted model
leaves R² unchanged (its coefficient collapses to ≈ −0.015, within noise), so it
was excluded to keep the law parsimonious and interpretable. The law uses only
`N` and `P`; `t` and `R` are not required.

## Implementation

`/app/law.py` implements the formula pointwise: `law` reads `N` and `P` from
each row and returns `{'dN_dt': r·N·(1−N/K) − a·N·P/(1+b·N)}`. Each row is mapped
independently, with no state, ordering, interpolation, or data access — only the
four fitted constants above.
