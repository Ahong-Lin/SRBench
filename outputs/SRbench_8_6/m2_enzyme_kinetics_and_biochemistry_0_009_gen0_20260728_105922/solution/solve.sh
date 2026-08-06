#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_009_gen0_20260728_105922

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
    catalytic_rate_constant = 5.0
    buffered_substrate_concentration = 100.0
    michaelis_constant = 50.0
    covalent_inactivation_rate_constant = 0.02
    inhibitor_concentration_after_pulse = 5.0
    inhibitor_addition_time = 40.0

    for point in input_data:
        t = point['t']
        E = point['E']
        EI = point['EI']
        P = point['P']
        dP_dt = catalytic_rate_constant*E*buffered_substrate_concentration/(michaelis_constant + buffered_substrate_concentration)
        predictions.append({'dP_dt': float(dP_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_009_gen0_20260728_105922 Reference Law

Target: `dP_dt`

Input variables: `t`, `E`, `EI`, `P`

Reference expression:

```text
dP_dt = catalytic_rate_constant*E*buffered_substrate_concentration/(michaelis_constant + buffered_substrate_concentration)
```

Fixed parameters: catalytic_rate_constant=5, buffered_substrate_concentration=100, michaelis_constant=50, covalent_inactivation_rate_constant=0.02, inhibitor_concentration_after_pulse=5, inhibitor_addition_time=40.
EOL
