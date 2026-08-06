#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_004_gen0_20260728_105921

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
    k_f = 0.1
    k_r = 1.0
    k_cat = 5.0
    E_tot = 1.0

    for point in input_data:
        t = point['t']
        S = point['S']
        ES = point['ES']
        P = point['P']
        dS_dt = -k_f*(E_tot - ES)*S + k_r*ES
        predictions.append({'dS_dt': float(dS_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_004_gen0_20260728_105921 Reference Law

Target: `dS_dt`

Input variables: `t`, `S`, `ES`, `P`

Reference expression:

```text
dS_dt = -k_f*(E_tot - ES)*S + k_r*ES
```

Fixed parameters: k_f=0.1, k_r=1, k_cat=5, E_tot=1.
EOL
