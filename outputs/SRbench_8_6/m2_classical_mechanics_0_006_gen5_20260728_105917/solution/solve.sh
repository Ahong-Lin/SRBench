#!/bin/bash
# Reference solution for m2_classical_mechanics_0_006_gen5_20260728_105917

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
    moment_of_inertia_1 = 1.0
    moment_of_inertia_2 = 2.0
    moment_of_inertia_3 = 3.0
    rotational_drag_coefficient = 0.05
    quadratic_rotational_drag_coefficient = 0.02
    linear_rotational_drag_anisotropy_strength = 0.5
    quadratic_rotational_drag_anisotropy_strength = 0.5
    rotational_drag_axis_misalignment_angle = 0.5235987755982988

    for point in input_data:
        t = point['t']
        omega1 = point['omega1']
        omega2 = point['omega2']
        omega3 = point['omega3']
        domega1_dt = ((moment_of_inertia_2 - moment_of_inertia_3)*omega2*omega3 - rotational_drag_coefficient*((1 + linear_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*cos(rotational_drag_axis_misalignment_angle)*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2) - (1 + linear_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*sin(rotational_drag_axis_misalignment_angle)*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)) - quadratic_rotational_drag_coefficient*sqrt((1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2)**2 + (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)**2 + (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_3/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*omega3**2)*((1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*cos(rotational_drag_axis_misalignment_angle)*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2) - (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*sin(rotational_drag_axis_misalignment_angle)*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)))/moment_of_inertia_1
        predictions.append({'domega1_dt': float(domega1_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_006_gen5_20260728_105917 Reference Law

Target: `domega1_dt`

Input variables: `t`, `omega1`, `omega2`, `omega3`

Reference expression:

```text
domega1_dt = ((moment_of_inertia_2 - moment_of_inertia_3)*omega2*omega3 - rotational_drag_coefficient*((1 + linear_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*cos(rotational_drag_axis_misalignment_angle)*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2) - (1 + linear_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*sin(rotational_drag_axis_misalignment_angle)*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)) - quadratic_rotational_drag_coefficient*sqrt((1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2)**2 + (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)**2 + (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_3/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*omega3**2)*((1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_1/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*cos(rotational_drag_axis_misalignment_angle)*(cos(rotational_drag_axis_misalignment_angle)*omega1 + sin(rotational_drag_axis_misalignment_angle)*omega2) - (1 + quadratic_rotational_drag_anisotropy_strength*(3*moment_of_inertia_2/(moment_of_inertia_1 + moment_of_inertia_2 + moment_of_inertia_3) - 1))*sin(rotational_drag_axis_misalignment_angle)*(-sin(rotational_drag_axis_misalignment_angle)*omega1 + cos(rotational_drag_axis_misalignment_angle)*omega2)))/moment_of_inertia_1
```

Fixed parameters: moment_of_inertia_1=1, moment_of_inertia_2=2, moment_of_inertia_3=3, rotational_drag_coefficient=0.05, quadratic_rotational_drag_coefficient=0.02, linear_rotational_drag_anisotropy_strength=0.5, quadratic_rotational_drag_anisotropy_strength=0.5, rotational_drag_axis_misalignment_angle=0.523599.
EOL
