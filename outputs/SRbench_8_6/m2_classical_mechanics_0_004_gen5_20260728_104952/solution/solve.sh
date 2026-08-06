#!/bin/bash
# Reference solution for m2_classical_mechanics_0_004_gen5_20260728_104952

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
    k = 0.4
    mu_r = 0.08
    C_drag = 0.06
    ramp_length = 2.0
    psi_speed = 0.05
    kappa_slip = 0.05
    beta_slip = 0.05
    C_bearing = 0.04
    lambda_visc = 0.15

    for point in input_data:
        theta = point['theta']
        a = g*(sin(theta) - mu_r*cos(theta))/(1 + k) - C_drag*g*sin(theta)**2/(1 + k) - (mu_r*g*cos(theta)/(1 + k))*psi_speed*g*sin(theta)*ramp_length - (kappa_slip*g*cos(theta)/(1 + k))*(g*sin(theta)*ramp_length)/(1 + beta_slip*g*cos(theta)) - (C_bearing*g*cos(theta)/(1 + k))*(1 - exp(-lambda_visc*g*sin(theta)*ramp_length))
        predictions.append({'a': float(a)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_004_gen5_20260728_104952 Reference Law

Target: `a`

Input variables: `theta`

Reference expression:

```text
a = g*(sin(theta) - mu_r*cos(theta))/(1 + k) - C_drag*g*sin(theta)**2/(1 + k) - (mu_r*g*cos(theta)/(1 + k))*psi_speed*g*sin(theta)*ramp_length - (kappa_slip*g*cos(theta)/(1 + k))*(g*sin(theta)*ramp_length)/(1 + beta_slip*g*cos(theta)) - (C_bearing*g*cos(theta)/(1 + k))*(1 - exp(-lambda_visc*g*sin(theta)*ramp_length))
```

Fixed parameters: g=9.81, k=0.4, mu_r=0.08, C_drag=0.06, ramp_length=2, psi_speed=0.05, kappa_slip=0.05, beta_slip=0.05, C_bearing=0.04, lambda_visc=0.15.
EOL
