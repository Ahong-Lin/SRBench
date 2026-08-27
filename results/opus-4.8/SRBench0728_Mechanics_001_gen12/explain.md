# Discovered Law: `dx_dt = v`

## Formula

$$\frac{dx}{dt} = v$$

The target `dx_dt` is exactly equal to the input variable `v`.

## Methodology

1. Loaded `/app/data/train_data.csv` (4500 rows) with pandas.
2. Computed the correlation of each input with the target. `v` had a
   correlation of exactly `1.000000` with `dx_dt`; all other variables were
   weaker (`Fh2`: -0.95, `Fh`: -0.61, `t`: 0.26, `x`: 0.02).
3. Tested the identity `dx_dt = v` directly:
   `max |dx_dt - v| = 0.0` across all rows — an exact match, not a fit.

## Interpretation

The system is an observed dynamical system where `x` is a position-like
coordinate and `v` is its velocity. The time derivative of position is, by
definition, the velocity: `dx/dt = v`. The other columns (`t`, `Fh`, `Fh2`)
are dynamical quantities (time, forces) that drive the acceleration `dv/dt`
but do not enter the equation for `dx/dt`.

## Parameters

None. The relationship is a parameter-free identity.

## Extrapolation

Because the law is an exact structural identity (the definition of velocity),
it is independent of the time window and remains valid for any right-hand
time segment of the experiment.
