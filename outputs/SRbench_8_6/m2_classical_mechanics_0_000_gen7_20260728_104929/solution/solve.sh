#!/bin/bash
# Reference solution for m2_classical_mechanics_0_000_gen7_20260728_104929

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
    gravity = 9.81
    link_length = 1.0
    quadratic_drag_factor = 0.05
    linear_drag_rate = 0.05
    link_to_bob_mass_ratio = 0.1
    bob_radius = 0.05
    aerodynamic_drag_relaxation_time = 0.2
    pivot_coulomb_friction_angular_acceleration = 0.05
    pivot_friction_transition_angular_speed = 0.1
    pivot_bearing_load_friction_angular_acceleration = 0.05

    for point in input_data:
        t = point['t']
        theta = point['theta']
        omega = point['omega']
        wake_drag_angular_acceleration = point['wake_drag_angular_acceleration']
        domega_dt = -(gravity/link_length)*((1 + link_to_bob_mass_ratio/2)/(1 + link_to_bob_mass_ratio/3 + 2*bob_radius**2/(5*link_length**2)))*sin(theta) - linear_drag_rate*omega - wake_drag_angular_acceleration - pivot_coulomb_friction_angular_acceleration*tanh(omega/pivot_friction_transition_angular_speed) - pivot_bearing_load_friction_angular_acceleration*Abs(cos(theta) + (link_length*omega**2/gravity)*((1 + link_to_bob_mass_ratio/2)/(1 + link_to_bob_mass_ratio)))*tanh(omega/pivot_friction_transition_angular_speed)
        predictions.append({'domega_dt': float(domega_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_000_gen7_20260728_104929 Reference Law

Target: `domega_dt`

Input variables: `t`, `theta`, `omega`, `wake_drag_angular_acceleration`

Reference expression:

```text
domega_dt = -(gravity/link_length)*((1 + link_to_bob_mass_ratio/2)/(1 + link_to_bob_mass_ratio/3 + 2*bob_radius**2/(5*link_length**2)))*sin(theta) - linear_drag_rate*omega - wake_drag_angular_acceleration - pivot_coulomb_friction_angular_acceleration*tanh(omega/pivot_friction_transition_angular_speed) - pivot_bearing_load_friction_angular_acceleration*Abs(cos(theta) + (link_length*omega**2/gravity)*((1 + link_to_bob_mass_ratio/2)/(1 + link_to_bob_mass_ratio)))*tanh(omega/pivot_friction_transition_angular_speed)
```

Fixed parameters: gravity=9.81, link_length=1, quadratic_drag_factor=0.05, linear_drag_rate=0.05, link_to_bob_mass_ratio=0.1, bob_radius=0.05, aerodynamic_drag_relaxation_time=0.2, pivot_coulomb_friction_angular_acceleration=0.05, pivot_friction_transition_angular_speed=0.1, pivot_bearing_load_friction_angular_acceleration=0.05.
EOL
