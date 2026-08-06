#!/bin/bash
# Reference solution for m2_classical_mechanics_0_005_gen3_20260728_105916

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
    G = 6.674e-11
    c = 299792458.0
    J2 = 0.01
    R_eq = 1000000.0

    for point in input_data:
        M = point['M']
        r = point['r']
        m = point['m']
        v_orb = sqrt(G*M/r) * sqrt(1 + m/M) * sqrt(1 - (3*G*M)/(2*r*c**2)) * sqrt(1 + (3*J2*R_eq**2)/(2*r**2))
        predictions.append({'v_orb': float(v_orb)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_005_gen3_20260728_105916 Reference Law

Target: `v_orb`

Input variables: `M`, `r`, `m`

Reference expression:

```text
v_orb = sqrt(G*M/r) * sqrt(1 + m/M) * sqrt(1 - (3*G*M)/(2*r*c**2)) * sqrt(1 + (3*J2*R_eq**2)/(2*r**2))
```

Fixed parameters: G=6.674e-11, c=2.99792e+08, J2=0.01, R_eq=1e+06.
EOL
