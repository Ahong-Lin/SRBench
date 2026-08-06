#!/bin/bash
# Reference solution for m2_population_ecology_0_006_gen5_20260728_105924

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
    c = 15.0
    z = 0.25
    A0 = 1.0
    D0 = 100.0
    r = 0.3
    h = 0.5
    H0 = 5.0
    u = 0.6
    P0 = 1.0

    for point in input_data:
        A = point['A']
        D = point['D']
        H = point['H']
        P_dist = point['P_dist']
        S = c * A**z * (1 - exp(-A / A0)) * exp(-D / D0) * (1 + r * D / (D0 + D)) * (1 + h * H / (H0 + H)) * (1 - u * (P_dist / (P0 + P_dist)) * (A0 / (A0 + A)))
        predictions.append({'S': float(S)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_006_gen5_20260728_105924 Reference Law

Target: `S`

Input variables: `A`, `D`, `H`, `P_dist`

Reference expression:

```text
S = c * A**z * (1 - exp(-A / A0)) * exp(-D / D0) * (1 + r * D / (D0 + D)) * (1 + h * H / (H0 + H)) * (1 - u * (P_dist / (P0 + P_dist)) * (A0 / (A0 + A)))
```

Fixed parameters: c=15, z=0.25, A0=1, D0=100, r=0.3, h=0.5, H0=5, u=0.6, P0=1.
EOL
