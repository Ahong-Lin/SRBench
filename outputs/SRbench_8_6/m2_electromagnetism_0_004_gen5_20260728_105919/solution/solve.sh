#!/bin/bash
# Reference solution for m2_electromagnetism_0_004_gen5_20260728_105919

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
    epsilon0 = 1.0
    c = 1.0

    for point in input_data:
        w = point['w']
        a = point['a']
        theta_obs = point['theta_obs']
        P = (q**2 * a**2 * w**4) / (12 * pi * epsilon0 * c**3) * (1 + (3/10) * (a * w / c)**2) * (1 - (a * w / c)**2)**(-3) * (1 + cos(theta_obs)**2) / 2 * (1 + (16/5) * (a * w / c)**2 * cos(theta_obs)**2 / (1 + cos(theta_obs)**2)) * (1 - (a*w/c)*cos(theta_obs))**(-4) * (1 - (a*w/c)**2)**2
        predictions.append({'P': float(P)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_004_gen5_20260728_105919 Reference Law

Target: `P`

Input variables: `w`, `a`, `theta_obs`

Reference expression:

```text
P = (q**2 * a**2 * w**4) / (12 * pi * epsilon0 * c**3) * (1 + (3/10) * (a * w / c)**2) * (1 - (a * w / c)**2)**(-3) * (1 + cos(theta_obs)**2) / 2 * (1 + (16/5) * (a * w / c)**2 * cos(theta_obs)**2 / (1 + cos(theta_obs)**2)) * (1 - (a*w/c)*cos(theta_obs))**(-4) * (1 - (a*w/c)**2)**2
```

Fixed parameters: q=1, epsilon0=1, c=1.
EOL
