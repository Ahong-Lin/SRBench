#!/bin/bash
# Reference solution for m2_classical_mechanics_0_001_gen0_20260728_104930

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
    gravitational_acceleration = 9.81
    quadratic_resistance_coefficient = 0.05
    mass = 1.0

    for point in input_data:
        t = point['t']
        s = point['s']
        v = point['v']
        dv_dt = gravitational_acceleration - quadratic_resistance_coefficient*v**2/mass
        predictions.append({'dv_dt': float(dv_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_001_gen0_20260728_104930 Reference Law

Target: `dv_dt`

Input variables: `t`, `s`, `v`

Reference expression:

```text
dv_dt = gravitational_acceleration - quadratic_resistance_coefficient*v**2/mass
```

Fixed parameters: gravitational_acceleration=9.81, quadratic_resistance_coefficient=0.05, mass=1.
EOL
