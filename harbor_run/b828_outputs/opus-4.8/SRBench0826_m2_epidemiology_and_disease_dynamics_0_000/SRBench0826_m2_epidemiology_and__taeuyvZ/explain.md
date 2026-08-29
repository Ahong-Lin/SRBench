# Discovering the law for `dI_dt`

## Summary

The data come from a compartmental outbreak model with a **saturating
(Holling type‑II) incidence**, not the textbook bilinear `βSI/N`. The
discovered pointwise law for the instantaneous change in the infectious pool is

```
dI/dt = c1 · S·I/(N+I)  +  c2 · I  +  c3 · S·I²/((N+I)·N)
```

with `N = S + E + I + R = 1000` (conserved) and

| coeff | value |
|-------|-------|
| c1 | 0.44102556 |
| c2 | −0.19678775 |
| c3 | −1.81822299 |

Equivalently, factoring the saturating shape,

```
dI/dt = S·I/(N+I) · (c1 + c3·I/N)  +  c2·I .
```

Fit quality on the training trajectory: **R² = 0.99974**, RMS = 0.028, and on
the last 300 points (the decay tail that most resembles the hidden right‑hand
test segment) RMS = 0.0021.

## How the model was identified

### 1. The population is closed
`S + E + I + R = 1000` for every row (std ≈ 1e‑13). No births/deaths/waning —
consistent with the problem statement.

### 2. `dI_dt` is the exact time‑derivative of the `I` column
A 4th‑order central finite difference of the `I` column reproduces the supplied
`dI_dt` to ~3e‑6 in the interior. So the target is genuinely `d(I)/dt` of a
smooth, deterministic trajectory — there is essentially no observational noise,
and any residual structure reflects the model form, not scatter.

### 3. The incidence is saturating, `0.5·S·I/(N+I)` (exact)
Differentiating `S` numerically and forming the effective transmission rate
`β_eff = −dS·N/(S·I)` reveals that it is **not constant**: it falls from 0.4995
at `I→0` to ≈0.468 at the peak. Crucially, `1/β_eff` is *exactly linear in `I`*:

```
1/β_eff = 2 + 2·I/N   ⇒   −dS/dt = 0.5·S·I/(N+I) .
```

Fitting `−dS/dt = 0.5·S·I/(N+I)` leaves a residual RMS of **4.8e‑7** — i.e. this
is the exact susceptible‑depletion / force‑of‑infection term. The transmission
saturates as the infectious pool grows, a common way to model behavioural
change or contact limitation during a large outbreak.

### 4. Why `dI_dt` cannot be the standard `σE − γI`
At `t = 0`: `E = 0`, `I = 1`, yet `dI_dt = +0.146 > 0` (I is rising). A standard
SEIR infectious equation `dI/dt = σE − γI` would give `−γ < 0` there. So `I`
receives inflow directly from an `S·I` infection term, and the classical SEIR
`I`‑equation is ruled out (confirmed: fitting `dI` to `(E, I)` gives RMS ≈ 1.1
with the wrong signs).

### 5. `E` and `R` do not enter the `I` balance
Timing: `I` peaks at t≈28.9, `E` peaks *later* at t≈32.1 — so `E` is **downstream**
of `I` (I → E), not a driver of it. Statistically, adding `E`, `E²`, `E·I`,
`√(EI)`, or `R` to the `S,I` model changes the residual by <0.001 and yields
coefficients ≈ 0. Hence `dI/dt` is a pointwise function of **`S` and `I` only**.
(A one‑sided derivative check at `t=0` shows the incoming infection flux splits,
with half going to `E` and half associated with the `I`/`R` side — consistent
with `E` being a parallel/relaxation class that never feeds back into `I`.)

### 6. Functional form of `f(S, I)`
Using the saturating building block `S·I/(N+I)` that governs `dS`, a compact
three‑term model captures essentially all of the signal:

```
dI/dt = c1·S·I/(N+I) + c2·I + c3·S·I²/((N+I)·N).
```

- `c1·S·I/(N+I)`: saturating infection inflow into `I`.
- `c2·I`: linear removal (recovery/progression out of `I`).
- `c3·S·I²/((N+I)·N)`: a second‑order saturation correction of the inflow
  (`S·I/(N+I)·(c1 + c3·I/N)`), which becomes negligible as `I→0`.

A broad search over polynomial and rational bases in `(S, I)`, plus free‑exponent
nonlinear fits (`a·S·I/(N+bI) − c·I/(1+dI/N)` etc.), never improved on
RMS ≈ 0.025–0.028; the small remaining residual is smooth and un‑correlated with
`E`/`R`, indicating a mild higher‑order term in `S,I` that is immaterial in the
test regime.

## Behaviour in the test (right‑hand) segment
The hidden test is later times, i.e. the decay tail where `I → 0` and
`S → S∞ ≈ 300`. There the law reduces to
`dI/dt ≈ (c1·S/N + c2)·I`, giving a per‑capita decay rate ≈ −0.065 near
`S = 300`, matching the observed tail rate (≈ −0.063). The `c3` term vanishes
as `I → 0`, so the model degrades gracefully and the fixed point `I = 0` gives
`dI/dt = 0` exactly. A 75/25 time‑split validation gave a held‑out (late‑time)
RMS of 0.0022, confirming reliable extrapolation into the test window.

## Implementation notes
`law.py` computes `N = S + E + I + R` per row (declared variables only), forms
the saturating denominator `D = N + I`, and evaluates the closed‑form expression
above. Each row is handled independently; there is no state, ordering
dependence, interpolation, table lookup, numerical differentiation, or data
access.
