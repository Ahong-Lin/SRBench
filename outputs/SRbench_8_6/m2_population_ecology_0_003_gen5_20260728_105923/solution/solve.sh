#!/bin/bash
# Reference solution for m2_population_ecology_0_003_gen5_20260728_105923

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
    r1 = 0.5
    r2 = 0.4
    K1 = 100.0
    K2 = 100.0
    alpha12 = 0.5
    alpha21 = 0.6
    a1 = 0.02
    h1 = 0.05
    a2 = 0.02
    h2 = 0.05
    m1 = 0.1
    b1 = 20.0
    s1 = 5.0
    c1 = 10.0
    d1 = 0.005
    e1 = 20.0
    f1 = 15.0
    g1 = 0.05
    rho = 1.0
    u1 = 0.1
    u2 = 0.1
    w = 20.0

    for point in input_data:
        t = point['t']
        N1 = point['N1']
        N2 = point['N2']
        R = point['R']
        dN1_dt = r1*N1*(1 - (N1 + alpha12*N2)/K1) - a1*N1*N2/(1 + h1*N1 + g1*R) - m1*N1**2/(b1 + N1) + s1*N1/(c1 + N2) - d1*N1**2*N2/((e1 + N1)*(f1 + N2))
        predictions.append({'dN1_dt': float(dN1_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_003_gen5_20260728_105923 Reference Law

Target: `dN1_dt`

Input variables: `t`, `N1`, `N2`, `R`

Reference expression:

```text
dN1_dt = r1*N1*(1 - (N1 + alpha12*N2)/K1) - a1*N1*N2/(1 + h1*N1 + g1*R) - m1*N1**2/(b1 + N1) + s1*N1/(c1 + N2) - d1*N1**2*N2/((e1 + N1)*(f1 + N2))
```

Fixed parameters: r1=0.5, r2=0.4, K1=100, K2=100, alpha12=0.5, alpha21=0.6, a1=0.02, h1=0.05, a2=0.02, h2=0.05, m1=0.1, b1=20, s1=5, c1=10, d1=0.005, e1=20, f1=15, g1=0.05, rho=1, u1=0.1, u2=0.1, w=20.
EOL
