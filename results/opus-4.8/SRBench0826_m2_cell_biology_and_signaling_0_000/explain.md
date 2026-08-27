# Discovered Law: Contact-Inhibited Cell Growth

## Result

```
dN/dt = r · N · ( 1 − (N / K)^θ )
```

with fitted constants

| symbol | meaning | value |
|--------|---------|-------|
| `r`    | intrinsic per-capita growth rate | `0.0843658` (1/time) |
| `K`    | carrying capacity (max confluent count) | `49298.6` |
| `θ`    | Richards shape exponent | `0.239350` |

**Training-set fit:** R² = 0.99808 (residual σ ≈ 4.4 on a target ranging 28–329).
**Forward extrapolation** (fit on first 80 % of time, scored on last 20 %, mimicking the hidden test split): R² ≈ 0.987.

This is the **theta-logistic** (a.k.a. **Richards / generalized-logistic**) growth model, the standard description of proliferation limited by contact inhibition on a finite surface.

## How I got there

### 1. Shape of the data
The data are a single growth trajectory: `t`, `N` (cell count), `S`, `A`, all essentially monotonic in time except `A`, which rises then falls. `N` climbs from 1000 to ~47,900 and saturates; `dN/dt` rises, peaks near `t ≈ 120`, then decays toward 0 — the classic sigmoid-derivative signature of density-limited growth.

### 2. Per-capita rate points to a carrying-capacity model
The per-capita rate `(dN/dt)/N` falls monotonically from ~0.042 toward ~0.0006 as the dish fills. That is the fingerprint of a `r·N·(1 − N/K)`-type law. A plain **logistic** fit gives K ≈ 47,900 (matching the observed plateau) but only **R² = 0.91** — the rate stays too high, too long, then drops too sharply for a symmetric logistic.

### 3. Adding a shape exponent
Introducing the Richards exponent θ,

```
dN/dt = r · N · (1 − (N/K)^θ)
```

fits with **R² = 0.998**. The estimate `θ ≈ 0.24 (< 1)` makes the growth curve strongly right-skewed: division stays vigorous until the culture is nearly confluent and then collapses quickly — biologically consistent with cells dividing almost freely until the surface is nearly saturated, at which point contact inhibition shuts division down abruptly.

### 4. Why `S` and `A` are **not** used
- `S` (occupied area) and `A` (available space per cell) are auxiliary state variables of the underlying process. Because the dataset is one trajectory, both are **collinear with `N`**, so they *appear* correlated with the rate but add no independent, generalizable information.
- Per-capita rate correlates with `log(A)` (0.99) purely because of this collinearity. Mechanistic space-based fits — Monod `r·N·A/(A+Kₘ)`, power laws `N·Aᶜ`, `r·N·log(A/A*)` — all fit the training path (R² 0.98–0.99) but **extrapolate disastrously** to the held-out later segment (test R² ranging from −0.3 to −150).
- The reason: in the late-time regime that the hidden test set occupies, `A` is nearly frozen (≈ 2.05–2.16) while the true rate still changes ~3×. `A` therefore carries almost no signal in the extrapolation region, whereas `N` still moves substantially and tracks the rate. Models keyed on `A` cannot see the tail; the `N`-based theta-logistic can.
- Adding a small `A` correction to the theta-logistic (`·A^c`, `c ≈ 0.056`) changes the hold-out score negligibly (0.9866 → 0.9873) and reduces to a constant rescaling of `r` in the test region, so it was dropped in favor of the simpler, more robust law.

### 5. Validation of the choice
A forward 80/20 split (train early times, test the later time segment — the same structure as the real evaluation) was used to rank candidates:

| model | test R² |
|-------|---------|
| **theta-logistic in N** | **0.987** |
| logistic·Aᶜ | 0.981 |
| plain logistic in N | −11.8 |
| Gompertz | −0.9 |
| Monod / A-based | −150 |

The theta-logistic in `N` is both the most accurate on the training data and by far the most stable extrapolator, so it is adopted as the governing law.

## Implementation
`law.py` implements `law(input_data)` returning `dN_dt = r·N·(1 − (N/K)^θ)` per row, using only `N`. The other columns are ignored by design.
