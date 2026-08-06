#!/bin/bash
# Reference solution for m2_classical_mechanics_0_003_gen15_20260728_104951

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
    omega0 = 1.0
    zeta = 1.05
    g_eff = 0.2
    beta_nl = 0.05
    c_quad = 0.05
    tau_relax = 3.0
    eta_relax = 0.5
    alpha_soft = 0.1
    gamma_relax = 0.2
    kappa_stiff = 0.3
    c_therm = 0.2
    T_amb = 0.0
    k_diss = 0.5
    chi_soft = 0.1
    theta_therm = 0.2
    theta_expand = 0.1
    mu_thermstiff = 0.1
    delta_arr = 0.2
    T_ref = 1.0
    c_quad_lin = 0.05
    T_env = 0.0
    T_env_amp = 0.5
    omega_env = 0.5

    for point in input_data:
        t = point['t']
        x = point['x']
        v = point['v']
        F_relax = point['F_relax']
        T_int = point['T_int']
        dx_dt = v
        predictions.append({'dx_dt': float(dx_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_003_gen15_20260728_104951 Reference Law

Target: `dx_dt`

Input variables: `t`, `x`, `v`, `F_relax`, `T_int`

Reference expression:

```text
dx_dt = v
```

Fixed parameters: omega0=1, zeta=1.05, g_eff=0.2, beta_nl=0.05, c_quad=0.05, tau_relax=3, eta_relax=0.5, alpha_soft=0.1, gamma_relax=0.2, kappa_stiff=0.3, c_therm=0.2, T_amb=0, k_diss=0.5, chi_soft=0.1, theta_therm=0.2, theta_expand=0.1, mu_thermstiff=0.1, delta_arr=0.2, T_ref=1, c_quad_lin=0.05, T_env=0, T_env_amp=0.5, omega_env=0.5.
EOL
