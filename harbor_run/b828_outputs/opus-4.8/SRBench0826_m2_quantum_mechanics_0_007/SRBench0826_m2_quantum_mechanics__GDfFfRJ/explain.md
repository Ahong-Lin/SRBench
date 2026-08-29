# Discovered Law — Coherent Tunneling Between Two Wells

## Result

The instantaneous right-hand side of the dynamics is, to machine precision,

```
dPr_dt = K · N + κ · (0.5 − Pr),      κ = 0.1
```

equivalently

```
dPr_dt = K · N + 0.05 − 0.1 · Pr.
```

This fits **all 4500 training rows with a maximum absolute error of ≈ 2 × 10⁻¹⁶**
(i.e. floating-point round-off — an exact relation, not a statistical fit).

## How it was found

1. **Target is a genuine time derivative.** A numerical `gradient(Pr, t)`
   matches the `dPr_dt` column with correlation 0.99999995, confirming that
   `dPr_dt = d(Pr)/dt`. The task is therefore to write this derivative as an
   explicit pointwise function of the observed variables.

2. **Dominant term.** Among single-feature fits, `dPr_dt ≈ K` already gives
   correlation 0.989. Testing products, `K · N` fit with coefficient
   **1.013 ≈ 1** and cut the residual roughly in half — pointing at `K·N` as
   the leading term with unit coefficient.

3. **Residual is purely linear in Pr.** The residual
   `r = dPr_dt − K·N` correlates with `Pr` at −1.0000000. A two-parameter
   least-squares fit gave

   ```
   r = −0.100000 · Pr + 0.050000
   ```

   with residual RMS ~5 × 10⁻¹⁷. Recognising `0.05 = 0.1 · 0.5`, this is
   exactly `κ (0.5 − Pr)` with `κ = 0.1`.

4. **Combining** the two pieces reproduces the target to round-off. Neither
   `t` nor `J` is needed once `Pr`, `K`, and `N` are known.

## Physical interpretation

For a particle tunneling between two nearly degenerate wells, the occupation
probability `Pr` of the initially empty well evolves under two competing
effects:

- **Coherent transfer `K · N`.** `K` is the coherence channel that carries the
  reversible, oscillatory probability current set by the tunneling coupling;
  `N` acts as a slowly varying envelope/normalization factor. Their product is
  the instantaneous tunneling current, which oscillates in sign and drives the
  coherent back-and-forth transfer described in the problem statement.

- **Relaxation `κ (0.5 − Pr)`.** A linear restoring term with rate `κ = 0.1`
  pulls the occupation toward the symmetric equilibrium value `Pr = 1/2`. This
  is why the oscillations in `Pr` decay toward 0.5 over the observed window
  (and why `Pr = 0` at `t = 0` starts with a positive slope `0.05 = κ·0.5`).

At equilibrium (`Pr = 1/2`) with no coherent current (`K = 0`) the derivative
vanishes, as expected.

## Notes on validity

- The law is strictly **pointwise**: each input row `(t, Pr, J, K, N)` maps to
  one `dPr_dt` independently. No trajectory processing, ordering, state, file
  reads, interpolation, or learned tables are used.
- Only the declared variables `Pr`, `K`, `N` and two fixed constants
  (`κ = 0.1` and the equilibrium `0.5`) appear. Because the relation is exact
  and analytic, it extrapolates to the held-out right-hand time segment
  without change.

## Implementation

See `law.py`:

```python
dPr_dt = K * N + 0.1 * (0.5 - Pr)
```
