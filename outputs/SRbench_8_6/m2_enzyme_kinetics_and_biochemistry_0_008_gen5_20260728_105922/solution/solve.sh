#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_008_gen5_20260728_105922

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
    V_max = 5.0
    K_feedback = 1.0
    hill_n = 4.0
    k_cat = 2.0
    K_M = 1.0
    k_prod = 1.0
    k_deg = 0.4
    k_dil = 0.05
    k_syn_E = 1.0
    K_ind = 1.0
    hill_m = 2.0
    k_deg_E = 0.3
    K_I_sub = 5.0
    K_IC = 4.0
    k_in_C = 1.5
    k_use_C = 0.4
    K_cout = 1.2
    hill_c = 2.5

    for point in input_data:
        t = point['t']
        X = point['X']
        Y = point['Y']
        E = point['E']
        C = point['C']
        dX_dt = V_max / (K_feedback**hill_n + Y**hill_n) * K_feedback**hill_n - k_cat * X * E * C / (K_M * (1 + C/K_IC) + X) - k_dil * X + k_cat * X * E * C * X / ((K_M * (1 + C/K_IC) + X) * (K_I_sub + X))
        predictions.append({'dX_dt': float(dX_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_008_gen5_20260728_105922 Reference Law

Target: `dX_dt`

Input variables: `t`, `X`, `Y`, `E`, `C`

Reference expression:

```text
dX_dt = V_max / (K_feedback**hill_n + Y**hill_n) * K_feedback**hill_n - k_cat * X * E * C / (K_M * (1 + C/K_IC) + X) - k_dil * X + k_cat * X * E * C * X / ((K_M * (1 + C/K_IC) + X) * (K_I_sub + X))
```

Fixed parameters: V_max=5, K_feedback=1, hill_n=4, k_cat=2, K_M=1, k_prod=1, k_deg=0.4, k_dil=0.05, k_syn_E=1, K_ind=1, hill_m=2, k_deg_E=0.3, K_I_sub=5, K_IC=4, k_in_C=1.5, k_use_C=0.4, K_cout=1.2, hill_c=2.5.
EOL
