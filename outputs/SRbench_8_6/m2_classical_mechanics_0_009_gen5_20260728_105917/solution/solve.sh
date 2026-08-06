#!/bin/bash
# Reference solution for m2_classical_mechanics_0_009_gen5_20260728_105917

cat > /app/law.py << 'EOL'
import numpy as np


def Piecewise(*pairs):
    for value, condition in pairs:
        if bool(condition):
            return value
    return pairs[-1][0]


pi = np.pi
sin = np.sin
cos = np.cos
tan = np.tan
asin = np.arcsin
acos = np.arccos
atan = np.arctan
atan2 = np.arctan2
sinh = np.sinh
cosh = np.cosh
tanh = np.tanh
exp = np.exp
log = np.log
sqrt = np.sqrt
Abs = abs


def Max(*args):
    return max(args)


def Min(*args):
    return min(args)


sign = np.sign
floor = np.floor
ceiling = np.ceil


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    predictions = []
    g = 9.81
    beta_speed = 0.05
    c_drag = 0.5
    a_contact = 0.8
    k_progress = 5.0

    for point in input_data:
        n = point['n']
        h0 = point['h0']
        e = point['e']
        v_wind = point['v_wind']
        h_n = h0 * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n + (v_wind**2)/(2*g) * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0))) - (c_drag/(2*g)) * (h0 * (2*g) * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n - v_wind**2 * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0)))) - (a_contact/(2*g)) * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0))) - (k_progress/(2*g)) * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0)))
        predictions.append({'h_n': float(h_n)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_009_gen5_20260728_105917 Reference Law

Target: `h_n`

Input variables: `n`, `h0`, `e`, `v_wind`

Reference expression:

```text
h_n = h0 * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n + (v_wind**2)/(2*g) * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0))) - (c_drag/(2*g)) * (h0 * (2*g) * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n - v_wind**2 * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0)))) - (a_contact/(2*g)) * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0))) - (k_progress/(2*g)) * (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n * (1 - (e**2 * exp(-beta_speed*sqrt(2*g*h0)))**n)/(1 - e**2 * exp(-beta_speed*sqrt(2*g*h0)))
```

Fixed parameters: g=9.81, beta_speed=0.05, c_drag=0.5, a_contact=0.8, k_progress=5.
EOL
