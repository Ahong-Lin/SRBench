# Discovered Law

## Formula

$$\frac{dx}{dt} = v$$

The output `dx_dt` is exactly equal to the input `v`.

## How it was found

Loading `/app/data/train_data.csv` and comparing the `dx_dt` column against
each candidate input, the `v` column matches `dx_dt` perfectly:

```
max |dx_dt - v| = 0.0   (over all 1500 rows)
```

There is no scaling factor, offset, or dependence on `t` or `x` — the match is
exact to floating-point precision.

## Interpretation

This is the kinematic definition of velocity: the rate of change of position
`x` with respect to time `t` is the velocity `v`. The columns `t` and `x` are
part of the underlying dynamical system (the data resemble a decaying/driven
oscillator given the range and shape of `x` and `v`), but the target quantity
`dx_dt` depends only on `v`.

## Parameters

None. The relationship is parameter-free: `dx_dt = v` with coefficient 1 and
intercept 0.
