#!/bin/bash
# Reference solution for m2_classical_mechanics_0_003_gen5_20260728_104952

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
    mass = 1.0
    linear_stiffness = 1.0
    cubic_stiffness = 0.5
    quintic_stiffness = 0.2
    seventh_order_stiffness = 0.1
    damping_coefficient = 0.2
    damping_relaxation_time = 2.0
    finite_extensibility_stiffness = 10.0
    limiting_extension = 1.2

    for point in input_data:
        t = point['t']
        x = point['x']
        v = point['v']
        viscoelastic_damping_force = point['viscoelastic_damping_force']
        dv_dt = -(linear_stiffness*x + cubic_stiffness*x**3 + quintic_stiffness*x**5 + seventh_order_stiffness*x**7 + finite_extensibility_stiffness*x*(x/limiting_extension)**8/(1 - (x/limiting_extension)**2) + viscoelastic_damping_force)/mass
        predictions.append({'dv_dt': float(dv_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_003_gen5_20260728_104952 Reference Law

Target: `dv_dt`

Input variables: `t`, `x`, `v`, `viscoelastic_damping_force`

Reference expression:

```text
dv_dt = -(linear_stiffness*x + cubic_stiffness*x**3 + quintic_stiffness*x**5 + seventh_order_stiffness*x**7 + finite_extensibility_stiffness*x*(x/limiting_extension)**8/(1 - (x/limiting_extension)**2) + viscoelastic_damping_force)/mass
```

Fixed parameters: mass=1, linear_stiffness=1, cubic_stiffness=0.5, quintic_stiffness=0.2, seventh_order_stiffness=0.1, damping_coefficient=0.2, damping_relaxation_time=2, finite_extensibility_stiffness=10, limiting_extension=1.2.
EOL
