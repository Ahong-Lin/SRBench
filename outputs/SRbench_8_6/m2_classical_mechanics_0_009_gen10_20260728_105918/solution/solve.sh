#!/bin/bash
# Reference solution for m2_classical_mechanics_0_009_gen10_20260728_105918

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
    axial_stiffness = 2000.0
    quadratic_compliance = 1.0
    cubic_compliance = 1.0
    quartic_compliance = 1.0
    quintic_compliance = 1.0
    sextic_compliance = 1.0
    septic_compliance = 1.0
    octic_compliance = 2.0

    for point in input_data:
        x = point['x']
        H = point['H']
        lam = point['lam']
        y = H/(lam*g)*(cosh(lam*g*x/H) - 1 - H*sinh(lam*g*x/H)**2/(2*axial_stiffness) + H**2*sinh(lam*g*x/H)**2*cosh(lam*g*x/H)/(2*axial_stiffness**2) - H**3*sinh(lam*g*x/H)**2*(3*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2)/(6*axial_stiffness**3) - quadratic_compliance*H**2*((lam*g*x/H)*sinh(lam*g*x/H) + (cosh(lam*g*x/H)**3 - 3*cosh(lam*g*x/H) + 2)/3)/(2*axial_stiffness**2) + quadratic_compliance*H**3*(sinh(lam*g*x/H)**2*cosh(lam*g*x*x/H)**2 + (lam*g*x/H)*sinh(lam*g*x/H)*cosh(lam*g*x/H))/(2*axial_stiffness**3) - cubic_compliance*H**3*sinh(lam*g*x/H)**2*(6 + sinh(lam*g*x/H)**2)/(12*axial_stiffness**3) + H**4/axial_stiffness**4*(sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(12*cosh(lam*g*x/H)**2 + 13*sinh(lam*g*x/H)**2)/24 - quadratic_compliance*(sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(4*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2) + (lam*g*x/H)*sinh(lam*g*x/H)*(2*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2))/4 + quadratic_compliance**2*cosh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H) + lam*g*x/H)**2/8 + cubic_compliance*sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(3 + sinh(lam*g*x/H)**2)/3 + quartic_compliance*((cosh(lam*g*x/H)**5 - 1)/5 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(2*sinh(lam*g*x/H)**2 + 5) + 3*lam*g*x/H)/8)) - quintic_compliance*H**5*sinh(lam*g*x/H)**2*(15 + 5*sinh(lam*g*x/H)**2 + sinh(lam*g*x/H)**4)/(30*axial_stiffness**5) + sextic_compliance*H**6/axial_stiffness**6*((cosh(lam*g*x/H)**7 - 1)/7 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(8*sinh(lam*g*x/H)**4 + 26*sinh(lam*g*x/H)**2 + 33) + 15*lam*g*x/H)/48) - septic_compliance*H**7*sinh(lam*g*x/H)**2*(140 + 70*sinh(lam*g*x/H)**2 + 28*sinh(lam*g*x/H)**4 + 5*sinh(lam*g*x/H)**6)/(280*axial_stiffness**7) + octic_compliance*H**8/axial_stiffness**8*((cosh(lam*g*x/H)**9 - 1)/9 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(48*sinh(lam*g*x/H)**6 + 200*sinh(lam*g*x/H)**4 + 326*sinh(lam*g*x/H)**2 + 279) + 105*lam*g*x/H)/384))
        predictions.append({'y': float(y)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_009_gen10_20260728_105918 Reference Law

Target: `y`

Input variables: `x`, `H`, `lam`

Reference expression:

```text
y = H/(lam*g)*(cosh(lam*g*x/H) - 1 - H*sinh(lam*g*x/H)**2/(2*axial_stiffness) + H**2*sinh(lam*g*x/H)**2*cosh(lam*g*x/H)/(2*axial_stiffness**2) - H**3*sinh(lam*g*x/H)**2*(3*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2)/(6*axial_stiffness**3) - quadratic_compliance*H**2*((lam*g*x/H)*sinh(lam*g*x/H) + (cosh(lam*g*x/H)**3 - 3*cosh(lam*g*x/H) + 2)/3)/(2*axial_stiffness**2) + quadratic_compliance*H**3*(sinh(lam*g*x/H)**2*cosh(lam*g*x*x/H)**2 + (lam*g*x/H)*sinh(lam*g*x/H)*cosh(lam*g*x/H))/(2*axial_stiffness**3) - cubic_compliance*H**3*sinh(lam*g*x/H)**2*(6 + sinh(lam*g*x/H)**2)/(12*axial_stiffness**3) + H**4/axial_stiffness**4*(sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(12*cosh(lam*g*x/H)**2 + 13*sinh(lam*g*x/H)**2)/24 - quadratic_compliance*(sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(4*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2) + (lam*g*x/H)*sinh(lam*g*x/H)*(2*cosh(lam*g*x/H)**2 + sinh(lam*g*x/H)**2))/4 + quadratic_compliance**2*cosh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H) + lam*g*x/H)**2/8 + cubic_compliance*sinh(lam*g*x/H)**2*cosh(lam*g*x/H)*(3 + sinh(lam*g*x/H)**2)/3 + quartic_compliance*((cosh(lam*g*x/H)**5 - 1)/5 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(2*sinh(lam*g*x/H)**2 + 5) + 3*lam*g*x/H)/8)) - quintic_compliance*H**5*sinh(lam*g*x/H)**2*(15 + 5*sinh(lam*g*x/H)**2 + sinh(lam*g*x/H)**4)/(30*axial_stiffness**5) + sextic_compliance*H**6/axial_stiffness**6*((cosh(lam*g*x/H)**7 - 1)/7 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(8*sinh(lam*g*x/H)**4 + 26*sinh(lam*g*x/H)**2 + 33) + 15*lam*g*x/H)/48) - septic_compliance*H**7*sinh(lam*g*x/H)**2*(140 + 70*sinh(lam*g*x/H)**2 + 28*sinh(lam*g*x/H)**4 + 5*sinh(lam*g*x/H)**6)/(280*axial_stiffness**7) + octic_compliance*H**8/axial_stiffness**8*((cosh(lam*g*x/H)**9 - 1)/9 - sinh(lam*g*x/H)*(sinh(lam*g*x/H)*cosh(lam*g*x/H)*(48*sinh(lam*g*x/H)**6 + 200*sinh(lam*g*x/H)**4 + 326*sinh(lam*g*x/H)**2 + 279) + 105*lam*g*x/H)/384))
```

Fixed parameters: g=9.81, axial_stiffness=2000, quadratic_compliance=1, cubic_compliance=1, quartic_compliance=1, quintic_compliance=1, sextic_compliance=1, septic_compliance=1, octic_compliance=2.
EOL
