#!/bin/bash
# Reference solution for m2_electromagnetism_0_001_gen5_20260728_105918

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
    R = 1.0
    C = 1.0
    V_emf = 2.0
    Q_0 = 5.0
    tau_a = 2.0
    I_leak = 1.0
    alpha_v = 5.0
    I_0 = 1.5
    n_id = 1.5

    for point in input_data:
        t = point['t']
        Q = point['Q']
        V_a = point['V_a']
        dQ_dt = -Q / (R * C) + V_a / (R * (Q_0 + C * V_a)) * Q - I_leak * tanh(Q / Q_0) - alpha_v * V_a**2 / (R * Q_0) - I_0 * (exp(Q / (n_id * Q_0)) - 1)
        predictions.append({'dQ_dt': float(dQ_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_001_gen5_20260728_105918 Reference Law

Target: `dQ_dt`

Input variables: `t`, `Q`, `V_a`

Reference expression:

```text
dQ_dt = -Q / (R * C) + V_a / (R * (Q_0 + C * V_a)) * Q - I_leak * tanh(Q / Q_0) - alpha_v * V_a**2 / (R * Q_0) - I_0 * (exp(Q / (n_id * Q_0)) - 1)
```

Fixed parameters: R=1, C=1, V_emf=2, Q_0=5, tau_a=2, I_leak=1, alpha_v=5, I_0=1.5, n_id=1.5.
EOL
