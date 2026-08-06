#!/bin/bash
# Reference solution for m2_classical_mechanics_0_006_gen2_20260728_105917

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
    N = 10.0
    mu_s = 0.4
    mu_k = 0.3
    v_ref = 1.0
    alpha_v = 0.2

    for point in input_data:
        F_app = point['F_app']
        F_net = Piecewise((0, F_app <= mu_s*N), (F_app - (mu_k + (mu_s - mu_k)*exp(-((F_app - mu_s*N)/(mu_k*N))/v_ref))*N*(1 + alpha_v*((F_app - mu_s*N)/(mu_k*N))), F_app > mu_s*N))
        predictions.append({'F_net': float(F_net)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_006_gen2_20260728_105917 Reference Law

Target: `F_net`

Input variables: `F_app`

Reference expression:

```text
F_net = Piecewise((0, F_app <= mu_s*N), (F_app - (mu_k + (mu_s - mu_k)*exp(-((F_app - mu_s*N)/(mu_k*N))/v_ref))*N*(1 + alpha_v*((F_app - mu_s*N)/(mu_k*N))), F_app > mu_s*N))
```

Fixed parameters: N=10, mu_s=0.4, mu_k=0.3, v_ref=1, alpha_v=0.2.
EOL
