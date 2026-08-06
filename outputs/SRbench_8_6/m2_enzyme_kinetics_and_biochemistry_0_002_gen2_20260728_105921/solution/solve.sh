#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_002_gen2_20260728_105921

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
    K = 10.0
    n = 3.0
    theta_leak = 0.1
    theta_inhib = 0.3
    Ki = 50.0
    m = 2.0

    for point in input_data:
        S = point['S']
        theta = S**n / (K**n + S**n) + theta_leak * K**n / (K**n + S**n) - theta_inhib * S**(n + m) / (Ki**(n + m) + S**(n + m))
        predictions.append({'theta': float(theta)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_002_gen2_20260728_105921 Reference Law

Target: `theta`

Input variables: `S`

Reference expression:

```text
theta = S**n / (K**n + S**n) + theta_leak * K**n / (K**n + S**n) - theta_inhib * S**(n + m) / (Ki**(n + m) + S**(n + m))
```

Fixed parameters: K=10, n=3, theta_leak=0.1, theta_inhib=0.3, Ki=50, m=2.
EOL
