# Discovered Law: Prey Dynamics in a Predator–Prey Reserve

## Result

The instantaneous prey growth rate is governed by the **Rosenzweig–MacArthur
model** — logistic self-limited growth minus predation with a saturating
(Holling type-II) functional response:

$$
\frac{dN}{dt} \;=\; r\,N\!\left(1-\frac{N}{K}\right)\;-\;\frac{a\,N\,P}{1+a\,h\,N}
$$

Fitted parameters (nonlinear least squares on `train_data.csv`):

| symbol | meaning | value |
|--------|---------|-------|
| `r` | intrinsic prey growth rate | **0.79803** |
| `K` | prey carrying capacity | **99.908** |
| `a` | predator attack (encounter) rate | **0.130544** |
| `h` | predator handling time | **0.168119** |

Derived quantities: maximum kill rate per predator `1/h ≈ 5.95`; prey density
at half-maximal predation `1/(a·h) ≈ 45.6`.

## Fit quality

- **R² = 0.99984** on the full training set (RMSE ≈ 0.058, MAE ≈ 0.034 vs. a
  target standard deviation of 4.57).
- **Generalization**: fitting on `t < 90` and predicting on `t ≥ 90` gives
  **R² = 0.9996** with virtually unchanged parameters — the law is not
  overfit to the left segment and extrapolates to the held-out right segment.

## Interpretation of each term

- **`r·N·(1 − N/K)`** — In the predator's absence the prey grow logistically:
  near-exponential when rare, leveling off at the carrying capacity
  `K ≈ 100`. This matches the observed booms that top out just below 100.
- **`a·N·P / (1 + a·h·N)`** — Predation. Encounters scale with the product of
  the two abundances (`N·P`), but each predator saturates at high prey density
  because it spends time handling prey (denominator `1 + a·h·N`). This
  saturation is what drives the recurring boom-and-bust cycles: predators
  cannot keep up during a prey boom, prey overshoot, predators then catch up
  and crash the prey, and the cycle repeats.

## Why `R` is not in the prey equation

The dataset supplies a fourth variable `R` (a slowly varying resource/auxiliary
state of the coupled system). It was tested thoroughly and is **not needed** for
the prey right-hand side:

- Adding linear/product terms in `R` to the fitted model improves R² only from
  0.99984 to 0.99985 (noise level).
- Using `R` to *drive* prey growth (`α·N·R`) or *replace* the predation term
  (`c·P·R`, `c·N·P·R`) is markedly worse (R² ≈ 0.53–0.67).
- The RM residuals (std ≈ 0.057) are not a simple polynomial function of
  `t, N, P, R` (a full quadratic-in-`R` regression explains only ~22% of them),
  consistent with them being integration/measurement artifacts rather than a
  missing `R`-dependent term.

`R` participates in the *coupled* system (it evolves alongside `N` and `P`), but
the **prey** flux `dN/dt` is closed in `N` and `P` alone.

## Alternatives considered and rejected

| model | form | R² |
|-------|------|----|
| Lotka–Volterra | `a·N − b·N·P` | 0.38 |
| Logistic + linear predation | `r·N(1−N/K) − b·N·P` | 0.83 |
| Holling type III | `r·N(1−N/K) − a·N²P/(1+a·h·N²)` | 0.95 |
| Beddington–DeAngelis | adds predator interference `+w·P` | 0.99989 (w≈0.008, negligible) |
| Resource-driven growth | `α·N·R − m·N − predation` | 0.67 |
| **Rosenzweig–MacArthur** | **logistic + Holling II** | **0.99984** |

Holling type-II is the clear winner; Beddington–DeAngelis's extra parameter is
statistically negligible, so the simpler RM form is reported.

## Implementation

`/app/law.py` implements the formula pointwise. `law([row])` reads `N` and `P`
from the single row and returns `[{"dN_dt": r·N(1−N/K) − a·N·P/(1+a·h·N)}]`. It
carries no state, does no I/O, and uses only fixed constants inferred above —
each row is mapped independently, satisfying the verifier's requirements.
