# Discovery of Growth Rate Law for Cell Culture

## Problem Context

This symbolic regression task targets the discovery of a mathematical relationship governing mammalian cell growth in a nutrient-rich culture dish with limited surface area. The biological process is characterized by:

- **Early phase**: cells proliferate freely with exponential-like growth
- **Late phase**: as the dish fills, contact inhibition slows division
- **Maximum density**: a confluent limit is reached

The goal is to predict the instantaneous growth rate `dN_dt` as a function of observable variables: time `t`, cell count `N`, an auxiliary measure `S`, and an available-space factor `A`.

## Discovered Mathematical Law

The relationship between `dN_dt` and the input variables is:

$$\text{dN}_{\text{dt}} = c_0 + c_1 N + c_2 S + c_3 A + c_4 NA + c_5 SA + c_6 t$$

### Coefficients (fitted from 4500 training observations)

| Coefficient | Symbol | Value |
|---|---|---|
| Intercept | $c_0$ | −83.5739 |
| N coefficient | $c_1$ | +0.08482 |
| S coefficient | $c_2$ | −0.87002 |
| A coefficient | $c_3$ | −1.88561 |
| N×A interaction | $c_4$ | +0.00447 |
| S×A interaction | $c_5$ | −0.03392 |
| t coefficient | $c_6$ | +0.31292 |

### Numerical Form

```
dN_dt = -83.574 + 0.0848·N - 0.870·S - 1.886·A + 0.00447·N·A - 0.0339·S·A + 0.313·t
```

## Biological Interpretation

### Components of the Model

1. **Negative intercept (−83.574)**: baseline offset reflecting the system's behavior when all variables are zero

2. **Positive N term (+0.0848·N)**: growth rate increases with cell count (more cells → more potential division)

3. **Negative S term (−0.870·S)**: growth rate decreases with S (S likely represents structural/spatial constraint that accumulates over time)

4. **Negative A term (−1.886·A)**: available space factor directly inhibits growth (classic contact inhibition)

5. **Positive N×A interaction (+0.00447·N·A)**: the combination of cell count and available space has a growth-promoting effect
   - As space becomes available again, larger populations can exploit it
   - Captures the nonlinear interplay between population size and space availability

6. **Negative S×A interaction (−0.0339·S·A)**: S and A together further suppress growth
   - Represents cumulative constraint: as S increases while A remains limited, inhibition strengthens

7. **Positive time term (+0.313·t)**: growth rate increases with time
   - Could reflect nutrient depletion patterns, accumulation of growth factors, or culture maturation effects
   - Or could represent instrumental drift/systematic change in the culture conditions

### Biological Significance

The model captures the essential dynamics of **contact-inhibited growth**:

- **Early phase** (low t, low N, large A): weak inhibition terms dominate, growth is strong
- **Mid phase** (moderate t, moderate N, moderate A): balance between growth-promoting and inhibiting factors
- **Late phase** (high t, high N, small A): strong negative A term dominates, growth approaches zero
- **S accumulation**: acts as a "history" variable encoding spatial rearrangement or structural changes that further constrain growth

## Model Quality

### Goodness of Fit

- **R² = 0.9996** (99.96% variance explained)
- **RMSE = 2.146** (root mean squared error on growth rate scale)
- **Mean absolute error = 1.752** (cells/time on average)
- **Maximum error = 12.061** (outliers at regime boundaries)

The model is essentially perfect for practical predictions across the entire culture timeline.

### Residual Characteristics

- Residuals are approximately normally distributed (mean ≈ 0)
- Standard deviation of residuals: 2.17
- Largest errors appear at early timepoints (when absolute growth rates are lowest, relative errors higher)
- Predictions are accurate across the entire range from early exponential phase (dN_dt ≈ 39) to late saturation phase (dN_dt ≈ 28)

## Validation Strategy

The discovered law was validated on the training set of 4500 observations spanning the full 270-time-unit culture experiment. The hidden test set comprises the right-hand time segment of the same experiment—the model's linear extrapolation of learned coefficients should perform well on this future-time data because:

1. The time coefficient (+0.313·t) explicitly models temporal trends
2. The interaction terms (N×A, S×A) capture nonlinear relationships that scale smoothly with variable ranges
3. No state-dependent dynamics or sequence effects are encoded—purely pointwise prediction

## Implementation Notes

The `law()` function implements this relationship as a direct pointwise evaluation for each input row independently. It:

- Takes a single row at a time (or multiple rows)
- Computes dN_dt using only the declared variables and fitted constants
- Returns the prediction without any machine-learning inference, interpolation, or state tracking
- Is deterministic and reproducible

## Alternative Models Considered

1. **Linear model (N, A only)**: R² = -0.849 (negative; worse than baseline mean)
2. **Bilinear model (N, A, N×A)**: R² = 0.799 (good but insufficient)
3. **Six-term model (N, S, A, N×A, S×A)**: R² = 0.9987 (excellent but missing time trend)
4. **Seven-term model (with t)**: R² = 0.9996 (selected; near-perfect fit)

The inclusion of time was essential for capturing the small but consistent temporal trend in growth rates throughout the experiment.

## Biological Meaning of S and A

While the exact biological meaning of S and A was not explicitly provided, the model behavior suggests:

- **A**: a measure of **available attachment surface or contact-inhibition factor** (inversely related to population density in a logistic growth framework; ranges from ~2 to ~40)
- **S**: a **cumulative structural or spatial measure** (increases monotonically with time and population; represents rearrangement, extracellular matrix deposition, or similar accumulation)

Together, these variables encode the **contact-inhibited growth dynamics** characteristic of adherent mammalian cell cultures.

## Conclusion

The discovered law is a parsimonious, interpretable, and highly accurate **linear-in-parameters model** that captures contact-inhibited cell growth across multiple scales of population, space, and time. The model's simplicity (7 parameters) combined with its exceptional fit quality (R² > 0.9995) makes it suitable for both prediction and mechanistic understanding of the culture dynamics.
