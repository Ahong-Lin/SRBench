#!/bin/bash
# Reference solution for m2_electromagnetism_0_000_gen5_20260728_105918

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
    epsilon0 = 8.854e-12
    relative_permittivity = 5.0
    radial_charge_gradient = 0.5
    dielectric_saturation_field = 10000000.0
    surface_polarization_suppression = 0.5
    interfacial_polarization_length = 5e-07

    for point in input_data:
        r = point['r']
        Q = point['Q']
        R = point['R']
        temperature = point['temperature']
        E_r = Piecewise((Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*relative_permittivity*(5 + 3*radial_charge_gradient)) + (1 - 1/relative_permittivity)*(Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*(5 + 3*radial_charge_gradient)) - dielectric_saturation_field*tanh(300*Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*dielectric_saturation_field*temperature*(5 + 3*radial_charge_gradient)))) + surface_polarization_suppression*(1 - 1/relative_permittivity)*dielectric_saturation_field*tanh(300*Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*dielectric_saturation_field*temperature*(5 + 3*radial_charge_gradient)))*exp(-(R - r)/interfacial_polarization_length), r <= R), (Q/(4*pi*epsilon0*r**2), True))
        predictions.append({'E_r': float(E_r)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_000_gen5_20260728_105918 Reference Law

Target: `E_r`

Input variables: `r`, `Q`, `R`, `temperature`

Reference expression:

```text
E_r = Piecewise((Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*relative_permittivity*(5 + 3*radial_charge_gradient)) + (1 - 1/relative_permittivity)*(Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*(5 + 3*radial_charge_gradient)) - dielectric_saturation_field*tanh(300*Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*dielectric_saturation_field*temperature*(5 + 3*radial_charge_gradient)))) + surface_polarization_suppression*(1 - 1/relative_permittivity)*dielectric_saturation_field*tanh(300*Q*(5*r/R**3 + 3*radial_charge_gradient*r**3/R**5)/(4*pi*epsilon0*dielectric_saturation_field*temperature*(5 + 3*radial_charge_gradient)))*exp(-(R - r)/interfacial_polarization_length), r <= R), (Q/(4*pi*epsilon0*r**2), True))
```

Fixed parameters: epsilon0=8.854e-12, relative_permittivity=5, radial_charge_gradient=0.5, dielectric_saturation_field=1e+07, surface_polarization_suppression=0.5, interfacial_polarization_length=5e-07.
EOL
