#!/bin/bash
# Reference solution for m2_electromagnetism_0_002_gen5_20260728_105918

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
    q = 1.0
    epsilon0 = 0.07957747154594767
    lambda_D = 1.0
    a_sphere = 0.1
    lambda_correction = 1.0
    quadrupole_coeff = 1.0
    p_dipole = 0.5
    dipole_coeff = 0.3

    for point in input_data:
        r = point['r']
        E = q / (4 * pi * epsilon0 * r**2) * exp(-r / lambda_D) * (1 + r / lambda_D) + q / (4 * pi * epsilon0 * lambda_D**2) * exp(-r / lambda_D) * (r / (2 * lambda_D**2)) * lambda_correction + q * a_sphere**2 / (4 * pi * epsilon0 * r**4) * exp(-r / lambda_D) * (3 + 3 * r / lambda_D + r**2 / lambda_D**2) * quadrupole_coeff + p_dipole / (4 * pi * epsilon0 * r**3) * exp(-r / lambda_D) * (2 + 2 * r / lambda_D + r**2 / lambda_D**2) * dipole_coeff
        predictions.append({'E': float(E)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_002_gen5_20260728_105918 Reference Law

Target: `E`

Input variables: `r`

Reference expression:

```text
E = q / (4 * pi * epsilon0 * r**2) * exp(-r / lambda_D) * (1 + r / lambda_D) + q / (4 * pi * epsilon0 * lambda_D**2) * exp(-r / lambda_D) * (r / (2 * lambda_D**2)) * lambda_correction + q * a_sphere**2 / (4 * pi * epsilon0 * r**4) * exp(-r / lambda_D) * (3 + 3 * r / lambda_D + r**2 / lambda_D**2) * quadrupole_coeff + p_dipole / (4 * pi * epsilon0 * r**3) * exp(-r / lambda_D) * (2 + 2 * r / lambda_D + r**2 / lambda_D**2) * dipole_coeff
```

Fixed parameters: q=1, epsilon0=0.0795775, lambda_D=1, a_sphere=0.1, lambda_correction=1, quadrupole_coeff=1, p_dipole=0.5, dipole_coeff=0.3.
EOL
