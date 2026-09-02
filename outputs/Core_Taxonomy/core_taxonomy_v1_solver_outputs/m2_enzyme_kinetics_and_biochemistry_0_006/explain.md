# Discovered Law: Enzyme Activity vs. pH and Temperature

## Formula

$$
A = b + \frac{A_{\max}}{1 + 10^{\,pK_{a1}(T) - pH} + 10^{\,pH - pK_{a2}(T)}}
$$

with temperature-dependent ionization constants

$$
pK_{a1}(T) = pK_{a1}^0 + c\,(T-300), \qquad pK_{a2}(T) = pK_{a2}^0 + c\,(T-300).
$$

## Fitted parameters

| Symbol | Meaning | Value |
|--------|---------|-------|
| $b$ | baseline activity floor | 7.99839 |
| $A_{\max}$ | bell amplitude | 91.89729 |
| $pK_{a1}^0$ | acidic-side pKa at 300 K | 6.03661 |
| $pK_{a2}^0$ | basic-side pKa at 300 K | 8.04093 |
| $c$ | pKa shift per K (both groups) | 0.0232992 |

(Temperature referenced to $T_{\text{ref}} = 300$ K.)

## Interpretation

This is the standard **diprotic (bell-shaped) enzyme pH-activity model**. Catalysis
requires one catalytic group to be deprotonated (governed by $pK_{a1}$, the acidic
limb) and another to be protonated (governed by $pK_{a2}$, the basic limb). The
fraction of enzyme in the correctly-ionized, catalytically-active state is

$$
f = \frac{1}{1 + 10^{pK_{a1}-pH} + 10^{pH-pK_{a2}}},
$$

which produces a bell that peaks near $pH \approx (pK_{a1}+pK_{a2})/2 \approx 7.0$
and decays on both the acidic and basic sides.

- **$A_{\max} \approx 91.9$** sets the peak turnover.
- **$b \approx 8.0$** is a residual/basal activity floor reached far from the optimum
  (the data never falls below ≈8).
- **Temperature effect:** the two pKa's shift *together* and *linearly* with
  temperature at rate $c \approx 0.023$ pH-units/K. This shifts the whole bell to
  higher pH as the buffer warms (≈0.23 pH units over the 278–323 K range) — a
  well-known consequence of the temperature dependence of ionization enthalpies of
  catalytic side chains. The bell width and amplitude are essentially
  temperature-independent.

## Methodology

1. **Exploration.** Binning `A` by `pH` revealed a clear bell peaking near pH 7 with
   a floor of ~8. Large scatter *within* each pH bin pointed to a second variable.
2. **Isolating the temperature effect.** At fixed pH (e.g. pH ≈ 5), `A` varied
   smoothly with `Temp`, indicating that temperature shifts the *position* of the
   bell rather than merely scaling its amplitude (amplitude/baseline temperature
   terms fit to ≈0).
3. **Model fitting.** A baseline + diprotic bell with linearly temperature-shifted
   pKa's was fit with `scipy.optimize.curve_fit`. Letting the two limbs shift at
   independent rates gave nearly identical rates ($c_1 \approx c_2 \approx 0.0233$),
   so a single shared shift parameter $c$ was adopted.

## Fit quality (training data)

- **R² = 0.99987**
- **RMSE = 0.316** (max abs error ≈ 1.32)

The `Temp` column enters only through the pKa shift; the residuals show no remaining
correlation with `pH` or `Temp`. The `A_noisy` column (σ ≈ 1.0) is a noisy replicate
and was not used for fitting.
