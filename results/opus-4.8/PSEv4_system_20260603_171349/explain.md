# Discovered Law

## Formula

$$\frac{dx}{dt} = v$$

The output `dx_dt` is exactly equal to the input `v`.

## Evidence

Loading `/app/data/train_data.csv` (1500 rows) and comparing columns directly:

- `dx_dt - v` has a maximum absolute difference of **0.0** across every row.
- `np.allclose(dx_dt, v)` returns `True`.
- The Pearson correlation between `v` and `dx_dt` is exactly `1.000000`, while `t` (0.47) and `x` (−0.61) are only partially correlated and are not needed.

## Interpretation

This is the kinematic definition of velocity: velocity is the time derivative of
position, so `dx/dt = v` holds identically. There are **no fitted parameters**.

The generating system appears to be a **damped harmonic oscillator**: `x` starts at
1.0 and undergoes a decaying oscillation over `t ∈ [0, 30]`, with `v` being its
instantaneous rate of change. While the full dynamics of that oscillator involve `t`,
`x`, and damping/frequency constants, the specific quantity requested here — `dx/dt` —
is simply `v` itself, requiring none of those constants.

## Model

```python
def law(input_data):
    return [{"dx_dt": row["v"]} for row in input_data]
```
