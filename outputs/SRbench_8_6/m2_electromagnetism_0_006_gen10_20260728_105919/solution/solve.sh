#!/bin/bash
# Reference solution for m2_electromagnetism_0_006_gen10_20260728_105919

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
    A_loop = 0.01
    second_harmonic_ratio = 0.3
    third_harmonic_ratio = 0.2
    fourth_harmonic_ratio = 0.15
    fifth_harmonic_ratio = 0.12
    sixth_harmonic_ratio = 0.1
    seventh_harmonic_ratio = 0.09
    eighth_harmonic_ratio = 0.08
    ninth_harmonic_ratio = 0.07
    tenth_harmonic_ratio = 0.08

    for point in input_data:
        B_0 = point['B_0']
        omega = point['omega']
        phi = point['phi']
        theta_incidence = point['theta_incidence']
        V_ind = -A_loop*B_0*omega*cos(theta_incidence)*(cos(phi) + 2*second_harmonic_ratio*cos(2*phi) + 3*third_harmonic_ratio*cos(3*phi) + 4*fourth_harmonic_ratio*cos(4*phi) + 5*fifth_harmonic_ratio*cos(5*phi) + 6*sixth_harmonic_ratio*cos(6*phi) + 7*seventh_harmonic_ratio*cos(7*phi) + 8*eighth_harmonic_ratio*cos(8*phi) + 9*ninth_harmonic_ratio*cos(9*phi) + 10*tenth_harmonic_ratio*cos(10*phi))
        predictions.append({'V_ind': float(V_ind)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_006_gen10_20260728_105919 Reference Law

Target: `V_ind`

Input variables: `B_0`, `omega`, `phi`, `theta_incidence`

Reference expression:

```text
V_ind = -A_loop*B_0*omega*cos(theta_incidence)*(cos(phi) + 2*second_harmonic_ratio*cos(2*phi) + 3*third_harmonic_ratio*cos(3*phi) + 4*fourth_harmonic_ratio*cos(4*phi) + 5*fifth_harmonic_ratio*cos(5*phi) + 6*sixth_harmonic_ratio*cos(6*phi) + 7*seventh_harmonic_ratio*cos(7*phi) + 8*eighth_harmonic_ratio*cos(8*phi) + 9*ninth_harmonic_ratio*cos(9*phi) + 10*tenth_harmonic_ratio*cos(10*phi))
```

Fixed parameters: A_loop=0.01, second_harmonic_ratio=0.3, third_harmonic_ratio=0.2, fourth_harmonic_ratio=0.15, fifth_harmonic_ratio=0.12, sixth_harmonic_ratio=0.1, seventh_harmonic_ratio=0.09, eighth_harmonic_ratio=0.08, ninth_harmonic_ratio=0.07, tenth_harmonic_ratio=0.08.
EOL
