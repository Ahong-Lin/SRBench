#!/bin/bash
# Reference solution for m2_electromagnetism_0_005_gen5_20260728_105919

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
    V_source = 12.0
    R = 2.0
    L = 0.1
    R_temp_coeff = 0.05
    L_sat_coeff = 0.01
    V_back_emf_coeff = 1.0
    I_ref = 3.0
    k_hyst = 0.5
    M_sat = 2.0
    tau_M = 0.1
    eddy_coeff = 2.0

    for point in input_data:
        t = point['t']
        I = point['I']
        M = point['M']
        dI_dt = (V_source - R*I - R_temp_coeff*I**3 - V_back_emf_coeff*tanh(I/I_ref) - k_hyst*M - eddy_coeff*(M_sat*tanh(I/I_ref) - M)/tau_M - L_sat_coeff*I**2*(V_source - R*I - R_temp_coeff*I**3 - V_back_emf_coeff*tanh(I/I_ref) - k_hyst*M - eddy_coeff*(M_sat*tanh(I/I_ref) - M)/tau_M)/L)/L
        predictions.append({'dI_dt': float(dI_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_005_gen5_20260728_105919 Reference Law

Target: `dI_dt`

Input variables: `t`, `I`, `M`

Reference expression:

```text
dI_dt = (V_source - R*I - R_temp_coeff*I**3 - V_back_emf_coeff*tanh(I/I_ref) - k_hyst*M - eddy_coeff*(M_sat*tanh(I/I_ref) - M)/tau_M - L_sat_coeff*I**2*(V_source - R*I - R_temp_coeff*I**3 - V_back_emf_coeff*tanh(I/I_ref) - k_hyst*M - eddy_coeff*(M_sat*tanh(I/I_ref) - M)/tau_M)/L)/L
```

Fixed parameters: V_source=12, R=2, L=0.1, R_temp_coeff=0.05, L_sat_coeff=0.01, V_back_emf_coeff=1, I_ref=3, k_hyst=0.5, M_sat=2, tau_M=0.1, eddy_coeff=2.
EOL
