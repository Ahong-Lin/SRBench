#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_005_gen5_20260728_105921

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
    A = 10000000000.0
    R = 8.314
    T_ref = 300.0
    m = 0.5
    Ea = 50000.0
    Theta_ref = 1.0
    K_ads0 = 0.1
    dH_ads = -30000.0
    C_S_ref = 0.1
    f_deact = 0.1
    Ea_deact = 80000.0
    K_prod0 = 0.1
    dH_prod = -20000.0
    beta_conv = 0.5
    gamma_diff = 100.0
    Ea_diff = 10000.0

    for point in input_data:
        T = point['T']
        C_S = point['C_S']
        k = A * (T / T_ref)**m * exp(-Ea / (R * T)) * (Theta_ref / (1 + K_ads0 * exp(-dH_ads / (R * T)) * (C_S / (1 + K_ads0 * exp(-dH_ads / (R * T)) * C_S_ref)))) * (1 + f_deact * exp(-Ea_deact / (R * T)))**(-1) * (1 + K_prod0 * exp(-dH_prod / (R * T)) * beta_conv * C_S)**(-1) * (1 + gamma_diff * sqrt(T / T_ref) * exp(-Ea_diff / (R * T)) / (1 + K_ads0 * exp(-dH_ads / (R * T)) * C_S))**(-1)
        predictions.append({'k': float(k)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_005_gen5_20260728_105921 Reference Law

Target: `k`

Input variables: `T`, `C_S`

Reference expression:

```text
k = A * (T / T_ref)**m * exp(-Ea / (R * T)) * (Theta_ref / (1 + K_ads0 * exp(-dH_ads / (R * T)) * (C_S / (1 + K_ads0 * exp(-dH_ads / (R * T)) * C_S_ref)))) * (1 + f_deact * exp(-Ea_deact / (R * T)))**(-1) * (1 + K_prod0 * exp(-dH_prod / (R * T)) * beta_conv * C_S)**(-1) * (1 + gamma_diff * sqrt(T / T_ref) * exp(-Ea_diff / (R * T)) / (1 + K_ads0 * exp(-dH_ads / (R * T)) * C_S))**(-1)
```

Fixed parameters: A=1e+10, R=8.314, T_ref=300, m=0.5, Ea=50000, Theta_ref=1, K_ads0=0.1, dH_ads=-30000, C_S_ref=0.1, f_deact=0.1, Ea_deact=80000, K_prod0=0.1, dH_prod=-20000, beta_conv=0.5, gamma_diff=100, Ea_diff=10000.
EOL
