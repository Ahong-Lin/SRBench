#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_000_gen0_20260728_105920

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
    Vmax = 1.0
    Km = 1.0

    for point in input_data:
        S = point['S']
        v = Vmax * S / (Km + S)
        predictions.append({'v': float(v)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_000_gen0_20260728_105920 Reference Law

Target: `v`

Input variables: `S`

Reference expression:

```text
v = Vmax * S / (Km + S)
```

Fixed parameters: Vmax=1, Km=1.
EOL
