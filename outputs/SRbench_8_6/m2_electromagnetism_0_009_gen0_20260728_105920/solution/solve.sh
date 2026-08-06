#!/bin/bash
# Reference solution for m2_electromagnetism_0_009_gen0_20260728_105920

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
    Ps = 0.25
    alpha = 5e-09

    for point in input_data:
        E = point['E']
        P = Ps * tanh(alpha * E / Ps)
        predictions.append({'P': float(P)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_009_gen0_20260728_105920 Reference Law

Target: `P`

Input variables: `E`

Reference expression:

```text
P = Ps * tanh(alpha * E / Ps)
```

Fixed parameters: Ps=0.25, alpha=5e-09.
EOL
