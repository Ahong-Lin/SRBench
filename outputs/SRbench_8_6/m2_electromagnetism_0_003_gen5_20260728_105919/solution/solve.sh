#!/bin/bash
# Reference solution for m2_electromagnetism_0_003_gen5_20260728_105919

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
    V = 1.0
    L = 0.01
    C = 1e-08
    R = 5.0
    R_s = 0.5
    R_L = 1000000.0
    D_f = 0.01
    alpha_L = 5e-09
    R_skin = 0.005
    C_stray = 1e-07

    for point in input_data:
        w = point['w']
        I = V / sqrt((R + R_s + R_L*w**2*L**2/(R_L**2 + w**2*L**2) + D_f/(C*w*(1 + D_f**2)) + R_skin*sqrt(w))**2 + (L*w*R_L**2/(R_L**2 + w**2*L**2) - 1/(C*w*(1 + D_f**2)) + alpha_L*w**2 - 1/(C_stray*w))**2)
        predictions.append({'I': float(I)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_003_gen5_20260728_105919 Reference Law

Target: `I`

Input variables: `w`

Reference expression:

```text
I = V / sqrt((R + R_s + R_L*w**2*L**2/(R_L**2 + w**2*L**2) + D_f/(C*w*(1 + D_f**2)) + R_skin*sqrt(w))**2 + (L*w*R_L**2/(R_L**2 + w**2*L**2) - 1/(C*w*(1 + D_f**2)) + alpha_L*w**2 - 1/(C_stray*w))**2)
```

Fixed parameters: V=1, L=0.01, C=1e-08, R=5, R_s=0.5, R_L=1e+06, D_f=0.01, alpha_L=5e-09, R_skin=0.005, C_stray=1e-07.
EOL
