#!/bin/bash
# Reference solution for m2_classical_mechanics_0_005_gen0_20260728_105916

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
    relative_exhaust_speed = 2500.0
    propellant_mass_flow_rate = 10.0
    gravitational_acceleration = 9.81

    for point in input_data:
        t = point['t']
        h = point['h']
        v = point['v']
        m = point['m']
        dv_dt = relative_exhaust_speed*propellant_mass_flow_rate/m - gravitational_acceleration
        predictions.append({'dv_dt': float(dv_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_005_gen0_20260728_105916 Reference Law

Target: `dv_dt`

Input variables: `t`, `h`, `v`, `m`

Reference expression:

```text
dv_dt = relative_exhaust_speed*propellant_mass_flow_rate/m - gravitational_acceleration
```

Fixed parameters: relative_exhaust_speed=2500, propellant_mass_flow_rate=10, gravitational_acceleration=9.81.
EOL
