# Discovering the settling-velocity law v(t)

## The discovered formula

The velocity of the settling sphere is described by a **three-mode exponential relaxation** toward a terminal velocity:

$$
v(t) = v_\infty - c_1 e^{-t/\tau_1} - c_2 e^{-t/\tau_2} - c_3 e^{-t/\tau_3}
$$

### Fitted parameters

| Parameter | Value |
|-----------|-------|
| $v_\infty$ | 10.792247712769347 |
| $c_1$ | 8.796514460387003 |
| $\tau_1$ | 1.0244985180076738 |
| $c_2$ | 5.486932688082194 |
| $\tau_2$ | 2.021017399049305 |
| $c_3$ | -3.57730703643592 |
| $\tau_3$ | 0.6463198783844387 |

Fit quality on the full training set: **RMS = 8.3×10⁻⁷**, max abs error = 4.2×10⁻⁶.

## Physical reasoning

The experiment is a sphere released from (near) rest and settling under gravity in a viscous fluid. The linearized equation of motion combines:

- **Stokes drag** (linear in velocity),
- **added mass** (effective inertia of displaced fluid),
- **Basset history force** (memory integral of past acceleration),
- **wall correction** (a multiplicative modification of the drag coefficient).

Such a linear system relaxes from its initial state toward the terminal (equilibrium) velocity $v_\infty$. The transient is a superposition of relaxation modes. While the pure Basset kernel formally produces `exp(a²t)·erfc(a√t)` modes, over the sampled window the response is captured essentially exactly by a small number of decaying exponential modes, which is the natural, interpretable pointwise form.

## Methodology

1. **Data inspection.** `v` rises monotonically from ≈0.14 at `t=0.01` toward a plateau near 10.1, a classic approach-to-terminal-velocity curve.
2. **Model screening.** A single exponential (RMS 0.033) and single/double `erfcx` history-force modes fit poorly. A sum of exponentials was tested with increasing order:
   - 1 exp → RMS 3.3×10⁻²
   - 2 exp → RMS 2.0×10⁻³
   - 3 exp → RMS 8.3×10⁻⁷ (converged; no further terms needed).
3. **Tail analysis.** The long-time residual `v_∞ − v` decays exponentially (constant semilog slope), not algebraically — consistent with a discrete set of relaxation modes rather than a `1/√t` algebraic tail.
4. **Extrapolation validation.** Fitting on `t ≤ 2.0` and predicting up to `t = 4.5` (a right-hand extrapolation mimicking the hidden test) gave max error 6×10⁻⁴; fitting on `t ≤ 3.0` gave 1×10⁻⁴. The terminal velocity is stable at $v_\infty \approx 10.80$ across all splits, confirming the model extrapolates reliably.
5. **Final fit.** Parameters were re-estimated by nonlinear least-squares (`scipy.optimize.curve_fit`) on the complete dataset.

## Implementation

`law.py` evaluates the closed-form expression pointwise for each input row independently — no state, interpolation, or data access — returning `{"v": value}` per row.
