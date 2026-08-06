#!/bin/bash
# Reference solution for m2_population_ecology_0_000_gen2_20260728_105922

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
    r = 0.8
    K = 50.0
    A = 3.0
    h = 3.0
    B = 4.0

    for point in input_data:
        t = point['t']
        N = point['N']
        dN_dt = r * N * (1 - N / K) * (N / A - 1) - h * N**2 / (B**2 + N**2)
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_000_gen2_20260728_105922 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`

Reference expression:

```text
dN_dt = r * N * (1 - N / K) * (N / A - 1) - h * N**2 / (B**2 + N**2)
```

Fixed parameters: r=0.8, K=50, A=3, h=3, B=4.
EOL
