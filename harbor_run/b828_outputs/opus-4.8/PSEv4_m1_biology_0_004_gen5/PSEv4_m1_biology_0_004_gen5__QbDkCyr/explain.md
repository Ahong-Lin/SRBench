# Discovered law for `X`

## Formula

$$
X(t, I_\text{light,prev}) = e^{-t/\tau}\big(a\cos\omega t + b\sin\omega t\big) \;+\; B \;+\; M\,e^{-t/\tau}\,I_\text{light,prev},
\qquad \omega = \frac{2\pi}{T}
$$

Equivalently, using amplitude/phase form: $X = A\,e^{-t/\tau}\cos(\omega t + \phi) + B + M\,e^{-t/\tau} I$, with $A=\sqrt{a^2+b^2}\approx2.16$ and $\phi=\operatorname{atan2}(-b,a)\approx-0.72$.

## Fitted parameters

| symbol | value | meaning |
|--------|-------|---------|
| $\tau$ | 30.29 | amplitude decay time constant |
| $T$    | 24.60 | oscillation period (≈ circadian day) |
| $a$    | 1.6233 | cosine quadrature amplitude |
| $b$    | 1.4219 | sine quadrature amplitude |
| $B$    | 0.0521 | equilibrium offset |
| $M$    | 0.1303 | transient light-response gain |

## Interpretation

The system is a **damped oscillator** with a period $T\approx24.6$ — a circadian‑type clock. Starting from an excited initial state near $t=0$ (amplitude ≈ 2.2), the oscillation **relaxes exponentially** toward an equilibrium value $B\approx0.05$ with a decay time $\tau\approx30$ (about 1.2 cycles per e‑fold). This decaying sinusoid explains the dominant structure: large swings early (X between −1.4 and +2.6 within the first day) shrinking to small fluctuations (±0.2) by the end of the record.

The previous light input contributes only a **small transient term** $M\,e^{-t/\tau}\,I$: light nudges the state while the oscillator is still energized early on, and its influence decays with the same envelope. Its gain is modest ($M\approx0.13$) and it matters only near $t=0$.

## Fit quality

On the training data the law reaches $R^2 = 0.856$ with a residual standard deviation of $0.215$. This residual is **flat across time and uncorrelated with both $t$ and $I_\text{light,prev}$** (essentially zero-mean Gaussian noise), so $0.215$ is the intrinsic noise floor of the dataset — the deterministic part is captured as fully as a pointwise function allows. The light term itself is small but gives a reproducible held-out improvement, confirming it is a genuine (if minor) signal rather than overfit noise.
