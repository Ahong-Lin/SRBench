# Discovering the law for `dN1_dt`

## Summary

The target is the instantaneous rate of change of species **N1** in a system of
two competing species (**N1**, **N2**) that also interacts with a third
antagonist variable **P1**. The recovered law is

```
dN1/dt = N1 · g(N1, N2, P1)
```

i.e. `dN1/dt` **factors through `N1`** (no population ⇒ no growth), and the
per-capita growth rate `g` is a smooth cubic function of the three densities.
This reproduces the training target to **RMSE ≈ 2·10⁻⁶**, **max abs error
≈ 1.6·10⁻⁵**, **R² = 1 − 3·10⁻¹²** — essentially generator precision.

## How I got there

### 1. The system is autonomous and competitive
Time `t` increases monotonically over a single trajectory (0 → 54); the data is
one settling experiment starting from a mixture. A model in `(N1, N2, P1)`
alone (no explicit `t`) reproduces the target exactly, confirming an
**autonomous ODE right-hand side** — as required, `dN1_dt = f(state)`.

### 2. Reconstructing the full system revealed the ecology
Numerically differentiating the other two observed variables and fitting
generalized Lotka–Volterra forms gave a decisive clue:

- **`dN2/dt` is an *exact* 2-species competition law** with clean round
  coefficients:
  `dN2/dt = 0.4·N2·(1 − N2/100 − 0.5·N1/100)` (RMSE ≈ 1·10⁻⁴, at the numeric
  noise floor). N1 suppresses N2; **P1 does not affect N2**.
- **`dP1/dt`** has negative intrinsic rate and grows with `N1`
  (`≈ P1·(−m + e·N1)`): **P1 is a specialist antagonist/consumer of N1**, not a
  competitor of N2.

So the picture is: **two competing plants N1–N2, plus an antagonist P1 that acts
only on N1.** This is why N1 (unlike N2) needs P1 to be explained: a plain
2-species competition fit of `dN1/dt` reaches only R²≈0.64, while adding the
`N1·P1` interaction jumps to R²≈0.998.

### 3. `dN1/dt` needs more than mass-action gLV
The generalized-LV form `dN1/dt = N1·(r − a₁₁N1 − a₁₂N2 − b·P1)` fits well
(R²≈0.998) but leaves a **smooth, structured residual of amplitude ≈0.04**.
I tested many mechanistic functional responses for the P1 interaction —
Holling type II (in N1 and in P1), Beddington–DeAngelis, ratio-dependent,
saturating competition — via grid and global (differential-evolution)
optimization. None removed the residual (all plateaued at RMSE 0.03–0.04), and
the best single correction term was the cross-interaction `N2·P1`. The residual
is effectively a **rational/higher-order function** of the state that a
polynomial expansion captures term by term.

### 4. Physically-constrained polynomial closed form
Because `dN1/dt` must vanish at `N1 = 0`, I imposed the factorization
`dN1/dt = N1·g(N1,N2,P1)` and fit `g` as a polynomial:

| model for `g` | full-data RMSE |
|---|---|
| linear (mass-action gLV) | 4.3·10⁻² |
| quadratic | 7.2·10⁻⁴ |
| **cubic** | **1.9·10⁻⁶** |

The **cubic per-capita rate** reaches generator precision. Crucially, the
N1-factored cubic is **well-conditioned** — all coefficients are ≤ 0.05 in
magnitude — whereas an unconstrained (free) cubic achieves the same fit only
with large, cancelling coefficients (up to ~3.4), which is both physically wrong
(nonzero growth at `N1=0`) and numerically fragile. I therefore use the
N1-factored cubic.

### 5. Generalization to the hidden test
The trajectory is a **damped inward spiral** converging to a coexistence
equilibrium (N1≈11–13, N2≈94, P1≈10.5). The hidden test is the right-hand (later)
time segment, i.e. the continuation of this spiral — its `(N1,N2,P1)` values lie
**inside the training hull** (interpolation). Forward-in-time holdout tests
(train early, predict late) confirm the N1-factored cubic generalizes best of
all candidates (holdout RMSE down to ~4·10⁻⁴ on the tightest-converged segment,
which is the closest analog to the real test where we train on all `t ≤ 54`).

## The law

```
dN1/dt = N1 · g(N1, N2, P1)

g(N1,N2,P1) =  0.0072189732
             − 0.0432695525·N1   + 0.0242586560·N2   + 0.0257484717·P1
             − 1.041853e-05·N1²  + 6.929614e-04·N1·N2 + 6.238669e-03·N1·P1
             − 3.780937e-04·N2²  − 3.474261e-03·N2·P1 + 1.327987e-02·P1²
             + 1.510016e-06·N1³  + 6.652185e-07·N1²·N2 − 3.736377e-05·N1²·P1
             − 4.036839e-06·N1·N2² − 3.556809e-05·N1·N2·P1 − 1.322285e-04·N1·P1²
             + 1.594800e-06·N2³  + 3.067201e-05·N2²·P1 − 1.333367e-04·N2·P1²
             + 7.237418e-06·P1³
```

**Interpretation.** The leading structure is Lotka–Volterra competition of N1
with itself and with N2, modulated by an antagonistic interaction with P1 (the
`N1·P1`, `P1²`, `N2·P1` terms dominate the P1 contribution). The higher-order
terms encode the saturating/rational nature of that antagonist interaction that
no single closed mechanistic response captured exactly; the cubic per-capita
polynomial is their compact, precise closed form.

## Implementation notes
- `law.py` implements `dN1/dt = N1 · g` with the coefficients above, mapping each
  row independently (the system is autonomous, so `t` is unused).
- No ML black box, lookup table, interpolation, differentiation, file reads,
  ordering dependence, or hidden state — only the declared variables
  `N1, N2, P1` and fixed constants inferred from training.
- Validated on the training set: RMSE 1.9·10⁻⁶, max abs error 1.6·10⁻⁵,
  R² = 0.9999999999966; verified order-independent on shuffled single-row calls.
