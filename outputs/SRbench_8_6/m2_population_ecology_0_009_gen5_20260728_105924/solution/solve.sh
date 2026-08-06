#!/bin/bash
# Reference solution for m2_population_ecology_0_009_gen5_20260728_105924

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
    r_sink = 0.2
    K_sink = 100.0
    m = 0.15
    a_sink = 0.01
    N_allee = 5.0
    d_sink = 0.4
    r_src = 0.3
    K_src = 200.0
    e = 0.05
    c_int = 0.002
    h_int = 0.05
    g_disp = 0.2
    N_leave = 20.0
    b_return = 0.5

    for point in input_data:
        t = point['t']
        Ns = point['Ns']
        Nsrc = point['Nsrc']
        dNs_dt = r_sink*Ns*(1 - Ns/K_sink) + m*Nsrc/(1 + a_sink*Ns)*(Ns/(Ns + N_allee)) - d_sink*Ns - c_int*Ns*Nsrc/(1 + h_int*Ns) - g_disp*Ns*(Ns/(Ns + N_leave)) + b_return*g_disp*Ns*(Ns/(Ns + N_leave))*(1 - Ns/K_sink)
        predictions.append({'dNs_dt': float(dNs_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_009_gen5_20260728_105924 Reference Law

Target: `dNs_dt`

Input variables: `t`, `Ns`, `Nsrc`

Reference expression:

```text
dNs_dt = r_sink*Ns*(1 - Ns/K_sink) + m*Nsrc/(1 + a_sink*Ns)*(Ns/(Ns + N_allee)) - d_sink*Ns - c_int*Ns*Nsrc/(1 + h_int*Ns) - g_disp*Ns*(Ns/(Ns + N_leave)) + b_return*g_disp*Ns*(Ns/(Ns + N_leave))*(1 - Ns/K_sink)
```

Fixed parameters: r_sink=0.2, K_sink=100, m=0.15, a_sink=0.01, N_allee=5, d_sink=0.4, r_src=0.3, K_src=200, e=0.05, c_int=0.002, h_int=0.05, g_disp=0.2, N_leave=20, b_return=0.5.
EOL
