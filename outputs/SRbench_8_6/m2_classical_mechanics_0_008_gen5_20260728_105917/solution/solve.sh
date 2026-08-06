#!/bin/bash
# Reference solution for m2_classical_mechanics_0_008_gen5_20260728_105917

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
    bearing_friction_torque = 0.01
    bearing_load_friction_length = 0.008
    cord_mass = 0.15
    pulley_mass_inertia_factor = 2.0

    for point in input_data:
        m1 = point['m1']
        m2 = point['m2']
        I = point['I']
        R = point['R']
        a2 = (m2 - m1)*g/(m1 + m2 + I/R**2) - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque)/(R*(m1 + m2 + I/R**2)) - cord_mass*((m2 - m1)*g - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque)/R)/((m1 + m2 + I/R**2)*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)) - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque))/(R*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)) - (bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)))/(R*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2 + cord_mass)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2 + cord_mass)*g)) - (bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)))/(R*(m1 + m2 + I/R**2 + cord_mass))
        predictions.append({'a2': float(a2)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_008_gen5_20260728_105917 Reference Law

Target: `a2`

Input variables: `m1`, `m2`, `I`, `R`

Reference expression:

```text
a2 = (m2 - m1)*g/(m1 + m2 + I/R**2) - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque)/(R*(m1 + m2 + I/R**2)) - cord_mass*((m2 - m1)*g - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque)/R)/((m1 + m2 + I/R**2)*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)) - bearing_friction_torque*tanh((m2 - m1)*g*R/bearing_friction_torque))/(R*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)) - (bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2)*g)))/(R*(m1 + m2 + I/R**2 + cord_mass)) - ((bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2 + cord_mass)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2 + cord_mass)*g)) - (bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)*tanh((m2 - m1)*g*R/(bearing_friction_torque + bearing_load_friction_length*(m1 + m2 + pulley_mass_inertia_factor*I/R**2)*g)))/(R*(m1 + m2 + I/R**2 + cord_mass))
```

Fixed parameters: g=9.81, bearing_friction_torque=0.01, bearing_load_friction_length=0.008, cord_mass=0.15, pulley_mass_inertia_factor=2.
EOL
