#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_005_gen7_20260728_105922

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
    A_chem = 10000000000000.0
    E_activation = 60000.0
    R_gas = 8.314
    Delta_Cp_activation = -500.0
    T_reference = 298.15
    sigma_E_activation = 5000.0
    T_tunneling = 500.0
    sigma_Delta_Cp_activation = 100.0
    rho_E_Delta_Cp_activation = 0.5
    tau_E_activation = 2000.0

    for point in input_data:
        T = point['T']
        k_chem = A_chem*exp(-E_activation/(R_gas*T) + (Delta_Cp_activation/R_gas)*(log(T/T_reference) - (T - T_reference)/T) + sigma_E_activation**2/(2*R_gas**2*T**2) + log((T_tunneling/(2*T))/sin(T_tunneling/(2*T))) + (sigma_Delta_Cp_activation**2/(2*R_gas**2))*(log(T/T_reference) - (T - T_reference)/T)**2 - (rho_E_Delta_Cp_activation*sigma_E_activation*sigma_Delta_Cp_activation/(R_gas**2*T))*(log(T/T_reference) - (T - T_reference)/T) + tau_E_activation/(R_gas*T) - tau_E_activation**2/(2*R_gas**2*T**2) - log(1 + tau_E_activation/(R_gas*T)))
        predictions.append({'k_chem': float(k_chem)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_005_gen7_20260728_105922 Reference Law

Target: `k_chem`

Input variables: `T`

Reference expression:

```text
k_chem = A_chem*exp(-E_activation/(R_gas*T) + (Delta_Cp_activation/R_gas)*(log(T/T_reference) - (T - T_reference)/T) + sigma_E_activation**2/(2*R_gas**2*T**2) + log((T_tunneling/(2*T))/sin(T_tunneling/(2*T))) + (sigma_Delta_Cp_activation**2/(2*R_gas**2))*(log(T/T_reference) - (T - T_reference)/T)**2 - (rho_E_Delta_Cp_activation*sigma_E_activation*sigma_Delta_Cp_activation/(R_gas**2*T))*(log(T/T_reference) - (T - T_reference)/T) + tau_E_activation/(R_gas*T) - tau_E_activation**2/(2*R_gas**2*T**2) - log(1 + tau_E_activation/(R_gas*T)))
```

Fixed parameters: A_chem=1e+13, E_activation=60000, R_gas=8.314, Delta_Cp_activation=-500, T_reference=298.15, sigma_E_activation=5000, T_tunneling=500, sigma_Delta_Cp_activation=100, rho_E_Delta_Cp_activation=0.5, tau_E_activation=2000.
EOL
