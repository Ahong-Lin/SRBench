# Discovering the law for `dI_dt` (seasonally forced infection)

## Summary

The instantaneous rate of change of the infectious population is well described
by a **seasonally forced transmission term plus density-dependent removal and an
immunity-coupling feedback**:

$$
\frac{dI}{dt} \;=\; \beta(t)\,S\,I \;-\; \gamma\, I \;-\; \varepsilon\, I\,C \;+\; \rho\, R,
\qquad
\beta(t) = \beta_0\,\bigl(1 + \alpha\cos(2\pi t + \phi)\bigr).
$$

Fitted constants (full training trajectory):

| symbol | value | role |
|--------|-------|------|
| $\beta_0$ | 1.514537 | baseline transmission scale |
| $\alpha$  | 0.593513 | relative seasonal forcing amplitude |
| $\phi$    | 0.026288 | small phase offset of the seasonal cycle |
| $\gamma$  | 0.475141 | linear per-capita removal of infectives |
| $\varepsilon$ | 6.985162 | extra removal of infectives $\propto$ burden $C$ |
| $\rho$    | 0.095145 | feedback from the recovered pool $R$ |

The angular frequency is exactly $\omega = 2\pi$, i.e. the environmental forcing
has **period 1** ("one year"), consistent with the stated yearly waves. Note
$\beta_0\alpha \approx 0.899$; this product (the *amplitude* of the oscillating
transmission term) is the sharply identified quantity.

**Accuracy:** on the training data $R^2 = 0.99994$, RMSE $= 1.6\times10^{-4}$,
max abs error $= 8\times10^{-4}$. On a held-out **later** time segment (train on
first 80 %, predict last 20 %) $R^2 = 0.99983$, and even a hard 50/50 split gives
$R^2 = 0.9996$ — so the law extrapolates to the right-hand test segment.

## How the law was found

### 1. The seasonal forcing period and amplitude
Scanning the frequency of a `S·I·cos(ωt)` term against `dI_dt` produced a sharp
optimum at $\omega \approx 6.283 = 2\pi$ (period 1). The coefficient on
`S·I·cos(2πt)` is extremely stable across every data subset (**0.898–0.900**),
fixing the seasonal amplitude of the transmission term. A tiny `S·I·sin` component
implies a small phase $\phi \approx 0.026$.

### 2. Cross-checking with the other state equations
Because the CSV also contains `S`, `R`, `C`, I reconstructed the companion
equations by finite differences (used only for *discovery*, not in `law.py`):

- $dS/dt = 0.02 - 0.02\,S + 0.1\,R - (3 + 0.9\cos 2\pi t)\,S I$  ($R^2 = 1.000$).
  This confirms the **seasonal transmission** $\beta(t)=3(1+0.3\cos 2\pi t)$ acting
  through the mass-action incidence $SI$, births/deaths at rate $0.02$, and waning
  immunity $R\to S$ at rate $0.1$.
- $dR/dt \approx 1.229\,I - 0.194\,R$ ($R^2 = 0.9997$): recovery inflow $\propto I$
  and outflow of the recovered pool.
- $dC/dt \approx 3.09\,S I - 0.386\,C$: `C` behaves like a **low-pass–filtered /
  accumulated infection burden** (an environmental/immunity memory variable),
  driven by the same incidence and relaxing at its own rate.

So `C` is an auxiliary burden variable, not a mass compartment, which is why the
four observed states are not conserved ($S+I+R+C$ is not constant).

### 3. Building `dI_dt`
Starting from the classic forced-SIR form $\beta(t)SI - \gamma I$ (which alone only
reaches $R^2\approx0.65$), residual analysis showed the remaining variation is
explained almost entirely by two additional couplings:

- a removal term proportional to $I\cdot C$ (infectives are cleared faster as the
  environmental burden $C$ grows), and
- a linear feedback in $R$.

Adding these two terms — and nothing else — takes the fit to $R^2 = 0.9994$ and,
crucially, makes it **robust under time extrapolation** (0.9996 on a 50/50 split).
Their coefficients are stable across data halves ($\varepsilon \approx 7$,
$\rho \approx 0.1$), unlike ad-hoc higher-order terms (e.g. $I^2$, $C R$) which
change sign between halves and were therefore rejected as trajectory-fitting
artifacts.

### 4. On parameter identifiability
Because the susceptible fraction stays in a narrow band ($S \in [0.41, 0.60]$), the
*constant* part of the incidence $\beta_0 S I$ is partly collinear with the linear
removal $\gamma I$ along the observed trajectory. Consequently the split of the
baseline between $\beta_0$ and $\gamma$ is only weakly constrained (individual
values drift modestly across subsets), while the **seasonal amplitude**
$\beta_0\alpha = 0.899$, the $I C$ coupling, and the $R$ feedback are all sharply
determined. The reported constants are the full-data least-squares solution; the
prediction is insensitive to the residual $\beta_0/\gamma$ ambiguity, which is why
the law extrapolates cleanly to the hidden later-time test segment.

## The implemented function

`law.py` evaluates, for each row independently,

```
beta = B0 * (1 + ALPHA * cos(2*pi*t + PHI))
dI_dt = beta * S * I - GAMMA * I - EPS * I * C + RHO * R
```

using only the declared variables `t, S, I, R, C` and the fitted constants above.
No data reads, interpolation, differentiation, ordering, or cross-call state are
used, satisfying the required pointwise-law form.
