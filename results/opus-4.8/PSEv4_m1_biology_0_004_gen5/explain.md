# Discovered law for `X`

## Result

`X` is a **deterministic function of the time variable `t` alone**. The best-fit
closed form is a superposition of one **decaying transient oscillation** and two
**persistent (undamped) oscillations** plus a constant baseline:

```
X(t) =  A1 · exp(-t/τ1) · cos(w1·t + p1)     # slow damped transient
      + Aa · cos(wa·t + pa)                   # persistent mode
      + Ab · cos(wb·t + pb)                   # persistent mode
      + c
```

### Fitted parameters

| symbol | value      | meaning |
|--------|-----------:|---------|
| `A1`   |  2.229699  | transient amplitude |
| `τ1`   | 29.311118  | transient decay time-constant |
| `w1`   |  0.257253  | transient angular frequency (period ≈ **24.42**) |
| `p1`   | -0.782699  | transient phase |
| `Aa`   |  0.153439  | amplitude of persistent mode a |
| `wa`   |  0.517307  | angular frequency of mode a (period ≈ **12.15**) |
| `pa`   | -0.727749  | phase of mode a |
| `Ab`   |  0.258192  | amplitude of persistent mode b |
| `wb`   |  1.240254  | angular frequency of mode b (period ≈ **5.07**) |
| `pb`   | -3.583885  | phase of mode b |
| `c`    |  0.071281  | constant offset |

**Fit quality:** R² = **0.991** on the full training set (residual std ≈ 0.054,
most of which is the non-sinusoidal shape of the early startup transient; the
late-time residual std is ≈ 0.014).

## How the law was discovered

1. **Structure of the inputs.** `t` is uniformly sampled from 0 to ≈151 in steps
   of 0.03361 (a single, time-ordered trajectory). `I_light_prev` is uniform
   white noise on [0, 2]: flat power spectrum, lag-1 autocorrelation ≈ −0.04, no
   periodicity.

2. **`I_light_prev` is a distractor.** Every attempt to use it failed:
   - Adding a linear term `g·I` to the fit gives `g ≈ 0.01` and **no** change in R².
   - The cross-correlation between `I` and the model residual is < 0.06 at **all**
     lags from −3 to +14 steps.
   - Discrete recurrences that included `I` assigned it a negligible coefficient
     (~0.003–0.007).

   Because the recovered oscillations are *pure sinusoids in `t`* that extrapolate
   cleanly in time (see step 4), they cannot be a response to random light input.
   `I_light_prev` is therefore statistically independent of `X` and is ignored.

3. **Spectral decomposition.** A whole-record FFT and a late-time (t > 120) FFT
   together reveal three components:
   - a **decaying** component near period 24.4 that dominates early and vanishes
     late — the system relaxing from its initial condition;
   - a **persistent** component at period ≈ 12.15 (≈ 2·w1);
   - a **persistent** component at period ≈ 5.07, which is the dominant feature at
     late times and explains the small steady-state fluctuations.

   These were fit jointly by non-linear least squares (`scipy.optimize.curve_fit`),
   giving R² = 0.991. Progressive model building confirmed the choice: a single
   damped sinusoid reaches only R² ≈ 0.85; adding the persistent 12.15 and 5.07
   modes raises it to 0.99.

4. **Generalisation check.** Fitting the model on only the first 60% of the
   trajectory and predicting the final 40% yields a residual std of ≈ 0.02. The
   law extrapolates in time, confirming it is a true function of `t` rather than a
   curve memorised to this particular noise realisation.

## Physical interpretation

The data are consistent with a lightly/under-damped dynamical system observed
after a perturbation: the large slow mode (period ≈ 24, τ ≈ 29) is the natural
transient decaying back toward equilibrium, while the two smaller persistent
oscillations (periods ≈ 12.15 and ≈ 5.07) are steady components that remain once
the transient has died out. The `I_light_prev` channel was recorded alongside the
signal but does not measurably drive `X` over the observed range.
