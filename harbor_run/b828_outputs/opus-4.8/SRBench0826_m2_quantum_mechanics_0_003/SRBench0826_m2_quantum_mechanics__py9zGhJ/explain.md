# Discovered law for coherent population transfer

## Result

The instantaneous right-hand side is reproduced exactly (to machine
precision) by a simple pointwise function of just two of the observed
variables — the excited-state population `P` and the coherence-like
variable `C`:

```
dP_dt = 0.4 * C - 0.4 * P - 0.3 * P**2
```

- **R² = 1.0** on the full training set.
- **Maximum absolute error ≈ 1.5e-16** (floating-point round-off), i.e.
  the relation is not a statistical fit but an algebraic identity present
  in the data.

## How it was found

1. **Correlation scan.** Against `dP_dt`, the strongest single-variable
   correlations were `C` (+0.56) and `N` (−0.66), while `t`, `W` were
   weak. This pointed to a coherent-transfer term (`C`) plus population
   dependence.
2. **Polynomial regression.** A least-squares fit of `dP_dt` on all
   linear and quadratic monomials of `{t, P, C, W, N}` returned R² = 1.0
   with only three non-negligible coefficients:
   - `C  → +0.4`
   - `P  → -0.4`
   - `P² → -0.3`
   Every other coefficient (including all terms in `t`, `W`, `N`, and the
   intercept) was zero to numerical precision.
3. **Refit on the three surviving terms** gave coefficients that were
   *exactly* `0.4`, `-0.4`, `-0.3` with a residual of ~2e-16, confirming a
   closed-form law rather than an approximation.

## Physical interpretation

For a two-level system driven by a resonant coupling, the excited-state
population grows through coherent exchange with the coupling/coherence
channel and is limited by a population-dependent back-transfer:

- `0.4 * C` — **coherent drive**: probability amplitude flows into the
  excited state at a rate set by the coupling strength (Rabi-like gain
  ~0.4) acting on the coherence variable `C`.
- `-0.4 * P` — **linear return**: reversible back-flow of population out
  of the excited state, proportional to how much is currently there.
- `-0.3 * P**2` — **saturation / nonlinear correction**: a quadratic term
  that curbs the transfer as the excited population builds up.

The variables `t`, `W`, and `N` carry no independent information for the
right-hand side once `P` and `C` are known (their influence is already
encoded through `C` and `P` along the trajectory), which is why they drop
out of the exact law.

## Implementation notes

`law()` in `/app/law.py` applies the formula independently to each input
row using the three fixed constants `A=0.4`, `B=0.4`, `D=0.3`. It uses
only the declared variables, carries no state between calls, performs no
I/O, numerical differentiation, or trajectory processing, and therefore
generalizes to the held-out right-hand time segment: predictions depend
only on the per-row values of `P` and `C`, which are supplied directly.
