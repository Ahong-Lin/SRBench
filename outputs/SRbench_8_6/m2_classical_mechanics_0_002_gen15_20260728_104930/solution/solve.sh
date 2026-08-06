#!/bin/bash
# Reference solution for m2_classical_mechanics_0_002_gen15_20260728_104930

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
    g = 9.81
    L = 1.0
    b = 0.0
    A_d = 0.0
    Omega_d = 1.0
    beta_q = 0.0
    epsilon_s = 0.05
    phi_d = 0.0
    I_p = 0.05
    k_p = 5.0
    c_p = 0.05
    gamma_c = 0.02
    kappa_p = 0.05
    tau_p = 0.02
    eta_p = 0.005
    gamma_p = 0.05
    mu_p = 0.05
    chi_ref = 1.0
    gamma_h = 0.02
    psi_ref = 0.1
    gamma_g = 0.02
    gamma_par = 0.3

    for point in input_data:
        t = point['t']
        theta = point['theta']
        omega = point['omega']
        psi = point['psi']
        chi = point['chi']
        dtheta_dt = omega
        predictions.append({'dtheta_dt': float(dtheta_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_002_gen15_20260728_104930 Reference Law

Target: `dtheta_dt`

Input variables: `t`, `theta`, `omega`, `psi`, `chi`

Reference expression:

```text
dtheta_dt = omega
```

Fixed parameters: g=9.81, L=1, b=0, A_d=0, Omega_d=1, beta_q=0, epsilon_s=0.05, phi_d=0, I_p=0.05, k_p=5, c_p=0.05, gamma_c=0.02, kappa_p=0.05, tau_p=0.02, eta_p=0.005, gamma_p=0.05, mu_p=0.05, chi_ref=1, gamma_h=0.02, psi_ref=0.1, gamma_g=0.02, gamma_par=0.3.
EOL
