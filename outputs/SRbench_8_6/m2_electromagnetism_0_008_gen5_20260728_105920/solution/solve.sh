#!/bin/bash
# Reference solution for m2_electromagnetism_0_008_gen5_20260728_105920

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
    mu = 1.0
    C = 1.0
    L0 = 1.0
    three = 3.0
    R = 0.3
    Gp = 0.01
    Cnl = 0.05
    Lsat = 5.0
    Isat = 5.0
    alphaR = 0.05
    Rth = 5.0
    kth = 2.0

    for point in input_data:
        t = point['t']
        V = point['V']
        IL = point['IL']
        phi = point['phi']
        Tth = point['Tth']
        dV_dt = (mu*(V - V**3/three) - IL - Gp*V - Cnl*V**2*(mu*(V - V**3/three) - IL - Gp*V)/C)/C
        predictions.append({'dV_dt': float(dV_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_008_gen5_20260728_105920 Reference Law

Target: `dV_dt`

Input variables: `t`, `V`, `IL`, `phi`, `Tth`

Reference expression:

```text
dV_dt = (mu*(V - V**3/three) - IL - Gp*V - Cnl*V**2*(mu*(V - V**3/three) - IL - Gp*V)/C)/C
```

Fixed parameters: mu=1, C=1, L0=1, three=3, R=0.3, Gp=0.01, Cnl=0.05, Lsat=5, Isat=5, alphaR=0.05, Rth=5, kth=2.
EOL
