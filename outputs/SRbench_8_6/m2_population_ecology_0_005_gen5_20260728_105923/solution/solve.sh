#!/bin/bash
# Reference solution for m2_population_ecology_0_005_gen5_20260728_105923

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
    r = 0.6
    K = 200.0
    A = 10.0
    h = 10.0
    b = 15.0
    m = 0.3
    c = 10.0
    g = 0.02
    s = 0.1
    q = 1.0
    d = 0.08
    w = 8.0
    T_h = 3.0

    for point in input_data:
        t = point['t']
        N = point['N']
        P_pred = point['P_pred']
        dN_dt = r * N * (1 - N / K) * (N / A - 1) - h * N**2 / (b**2 + N**2 + w * T_h * P_pred * N) - m * N / (c + N) + g * P_pred * N**2 / (b**2 + N**2 + w * T_h * P_pred * N)
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_005_gen5_20260728_105923 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`, `P_pred`

Reference expression:

```text
dN_dt = r * N * (1 - N / K) * (N / A - 1) - h * N**2 / (b**2 + N**2 + w * T_h * P_pred * N) - m * N / (c + N) + g * P_pred * N**2 / (b**2 + N**2 + w * T_h * P_pred * N)
```

Fixed parameters: r=0.6, K=200, A=10, h=10, b=15, m=0.3, c=10, g=0.02, s=0.1, q=1, d=0.08, w=8, T_h=3.
EOL
