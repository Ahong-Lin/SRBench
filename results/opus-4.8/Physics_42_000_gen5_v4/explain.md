# Settling velocity of a sphere: discovered law

## Formula

$$v(t) = A\left(1 - e^{-(t/\tau)^{p}}\right) \;-\; B\,e^{-t/\tau_2}$$

with fitted parameters:

| parameter | value | meaning |
|-----------|-------|---------|
| $A$      | 10.6153 | terminal (asymptotic) velocity |
| $\tau$   | 1.5818  | dominant relaxation time |
| $p$      | 1.0496  | stretching exponent (≈1) |
| $B$      | −0.1177 | amplitude of the fast transient |
| $\tau_2$ | 0.2927  | fast-transient time constant |

Because $B<0$, the last term *adds* a small fast rise at early times.

## Methodology

1. **Shape inspection.** The data rise monotonically from $v\approx0.14$ at
   $t=0.01$ toward a plateau of $\approx10.1$ at $t=4.5$ — a classic approach to
   a terminal velocity.

2. **Baseline.** A single exponential $A(1-e^{-t/\tau})$ fits reasonably
   (RMSE ≈ 0.039) but leaves a systematic, sign-alternating residual,
   indicating more than one time scale — consistent with the stated physics
   (drag + added-mass + Basset history + wall correction produce a fast initial
   transient superposed on the main relaxation).

3. **Model search with extrapolation validation.** Since the model is graded on
   the *right* extrapolation segment, I held out the largest-$t$ data (cuts at
   $t=3.0, 3.5, 4.0$), fit on the left, and measured test RMSE. Candidates:
   double exponential (degenerated to a single mode), Basset/BBO
   $e^{w t}\,\mathrm{erfc}(\sqrt{wt})$ modes (poor — the tail is exponential, not
   algebraic), stretched exponential, and stretched-exponential + fast
   transient.

4. **Winner.** The stretched exponential plus a fast exponential transient gave
   the most consistent held-out extrapolation error (test RMSE ≈ 0.013–0.018
   across all cuts, versus 0.006–0.041 for the plain stretched form and ≈0.09
   for a single exponential). It also has a clean physical reading: the main
   term is the drag/added-mass relaxation toward terminal velocity, and the
   short-$\tau_2$ term captures the fast initial history-force transient.

5. **Final fit.** Refit on the full dataset with `scipy.optimize.curve_fit`.

## Fit quality (full dataset)

- RMSE ≈ 0.0041
- Max absolute error ≈ 0.022

The stretching exponent $p\approx1.05$ shows the relaxation is very nearly, but
not exactly, a simple exponential — the mild departure is the fingerprint of the
history/wall corrections.
