#!/bin/bash
# Reference solution for m2_classical_mechanics_0_001_gen12_20260728_104929

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
    omega = 1.0
    beta = 0.05
    gamma = 0.02
    delta = 0.02
    alpha = 0.1
    tau_h = 1.0
    epsilon = 0.05
    alpha2 = 0.05
    tau_h2 = 5.0
    kappa = 0.05
    eta = 0.1
    mu = 0.1
    chi = 0.1
    sigma = 0.05
    lambda_s = 1.0
    nu = 0.5

    for point in input_data:
        t = point['t']
        x = point['x']
        v = point['v']
        Fh = point['Fh']
        Fh2 = point['Fh2']
        dx_dt = v
        predictions.append({'dx_dt': float(dx_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_001_gen12_20260728_104929 Reference Law

Target: `dx_dt`

Input variables: `t`, `x`, `v`, `Fh`, `Fh2`

Reference expression:

```text
dx_dt = v
```

Fixed parameters: omega=1, beta=0.05, gamma=0.02, delta=0.02, alpha=0.1, tau_h=1, epsilon=0.05, alpha2=0.05, tau_h2=5, kappa=0.05, eta=0.1, mu=0.1, chi=0.1, sigma=0.05, lambda_s=1, nu=0.5.
EOL
