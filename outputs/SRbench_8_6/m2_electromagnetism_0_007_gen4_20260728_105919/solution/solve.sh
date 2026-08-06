#!/bin/bash
# Reference solution for m2_electromagnetism_0_007_gen4_20260728_105919

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
    mu0 = 1.2566370614e-06
    a_wire = 0.001
    lambda_screen = 0.05
    mu_permeability_medium = 1e-05
    B_sat = 0.5

    for point in input_data:
        d = point['d']
        I1 = point['I1']
        I2 = point['I2']
        theta_tilt = point['theta_tilt']
        F = mu0 * I1 * I2 / (2 * pi * d) * (1 + a_wire**2 / d**2) * cos(theta_tilt) * exp(-d / lambda_screen) * (1 + (mu0 * I2 / (2 * pi * d))**2 / (2 * mu_permeability_medium * B_sat**2))
        predictions.append({'F': float(F)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_007_gen4_20260728_105919 Reference Law

Target: `F`

Input variables: `d`, `I1`, `I2`, `theta_tilt`

Reference expression:

```text
F = mu0 * I1 * I2 / (2 * pi * d) * (1 + a_wire**2 / d**2) * cos(theta_tilt) * exp(-d / lambda_screen) * (1 + (mu0 * I2 / (2 * pi * d))**2 / (2 * mu_permeability_medium * B_sat**2))
```

Fixed parameters: mu0=1.25664e-06, a_wire=0.001, lambda_screen=0.05, mu_permeability_medium=1e-05, B_sat=0.5.
EOL
