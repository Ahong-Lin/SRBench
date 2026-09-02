# Discovered Law: Cooperative (Hill) Activation of a Kinase

## Formula

$$A(X) = A_0 + (A_{\max} - A_0)\,\frac{X^{n}}{K^{n} + X^{n}}$$

This is a **leaky Hill function**, the standard model for a switch-like,
cooperatively activated response.

## Fitted parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| $A_{\max}$ | 0.83547 | Active fraction at saturating stimulus (high $X$) |
| $K$        | 6.15023 | Stimulus level at the half-way point of the transition |
| $n$        | 1.79791 | Hill coefficient — cooperativity / sharpness of the switch |
| $A_0$      | 0.05590 | Basal active fraction at low stimulus (leak) |

## Interpretation

- **Below threshold** ($X \ll K$): $A \to A_0 \approx 0.056$ — almost none of the
  kinase is active (a small basal leak).
- **Transition** ($X \approx K \approx 6.15$): the active fraction rises abruptly.
- **Above threshold** ($X \gg K$): $A \to A_{\max} \approx 0.835$ — near-full
  activation.
- The **Hill coefficient** $n \approx 1.8 > 1$ encodes the cooperative,
  multi-step nature of the activation cascade: a single Michaelis–Menten step
  would give $n = 1$ and a much gentler curve, whereas $n>1$ produces the
  observed sharp, sigmoidal switch.

## Methodology

1. Loaded `train_data.csv` (4500 rows). `X` spans 0.1–40; the clean target `A`
   ranges 0.051–0.811 and is sigmoidal in $X$, consistent with saturation below
   1 (hence an explicit $A_{\max}$ and basal $A_0$ rather than a bare Hill).
2. Fit candidate forms with `scipy.optimize.curve_fit`:
   - Bare Hill $A_{\max}X^n/(K^n+X^n)$: RMSE 0.0086 (systematic low-$X$ error).
   - **Leaky Hill (above): RMSE 0.00123, max error 0.0050 — chosen.**
   - A two-Hill sum reduced RMSE slightly but produced degenerate,
     non-interpretable parameters (a spurious power-law term), so it was
     rejected as overfitting.
3. The measurement noise in the dataset (from the `A_noisy` column) has
   $\sigma \approx 0.010$. The chosen model's RMSE against the clean signal
   (0.0012) is ~8× smaller than this noise floor, so the residual structure is
   negligible and the model is essentially exact for the underlying law.

## Implementation

`/app/law.py` evaluates the formula pointwise on each input row using the
fixed fitted constants above — no data access, state, or ordering dependence.
