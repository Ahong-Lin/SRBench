#!/bin/bash
# Reference solution for m2_classical_mechanics_0_007_gen5_20260728_105917

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
    restitution_coefficient = 0.8
    viscoelastic_loss_coefficient = 0.3
    adhesive_separation_energy = 0.05
    plastic_yield_speed = 3.0
    plastic_dissipation_fraction = 0.2
    impact_obliquity_angle = 0.5235987755982988

    for point in input_data:
        m1 = point['m1']
        m2 = point['m2']
        u1 = point['u1']
        u2 = point['u2']
        v1_out = u1*sin(impact_obliquity_angle)**2 + cos(impact_obliquity_angle)*((m1*u1*cos(impact_obliquity_angle) - m2*u2*cos(impact_obliquity_angle) - restitution_coefficient*m2*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)))/(m1 + m2) + m2/(m1 + m2)*(restitution_coefficient*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)) - sqrt(Max((restitution_coefficient*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)))**2 - 2*adhesive_separation_energy/(m1*m2/(m1 + m2)) - plastic_dissipation_fraction*Max(((u1 + u2)*cos(impact_obliquity_angle))**2 - plastic_yield_speed**2, 0), 0))))
        predictions.append({'v1_out': float(v1_out)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_007_gen5_20260728_105917 Reference Law

Target: `v1_out`

Input variables: `m1`, `m2`, `u1`, `u2`

Reference expression:

```text
v1_out = u1*sin(impact_obliquity_angle)**2 + cos(impact_obliquity_angle)*((m1*u1*cos(impact_obliquity_angle) - m2*u2*cos(impact_obliquity_angle) - restitution_coefficient*m2*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)))/(m1 + m2) + m2/(m1 + m2)*(restitution_coefficient*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)) - sqrt(Max((restitution_coefficient*(u1 + u2)*cos(impact_obliquity_angle)*exp(-viscoelastic_loss_coefficient*((u1 + u2)*cos(impact_obliquity_angle))**(1/5)/(m1*m2/(m1 + m2))**(2/5)))**2 - 2*adhesive_separation_energy/(m1*m2/(m1 + m2)) - plastic_dissipation_fraction*Max(((u1 + u2)*cos(impact_obliquity_angle))**2 - plastic_yield_speed**2, 0), 0))))
```

Fixed parameters: restitution_coefficient=0.8, viscoelastic_loss_coefficient=0.3, adhesive_separation_energy=0.05, plastic_yield_speed=3, plastic_dissipation_fraction=0.2, impact_obliquity_angle=0.523599.
EOL
