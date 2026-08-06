#!/bin/bash
# Reference solution for m2_classical_mechanics_0_000_gen5_20260728_104929

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
    drag_coefficient = 0.3
    cart_mass = 100.0
    rolling_resistance_coefficient = 0.01
    gravity = 9.81
    velocity_scale = 0.5
    air_density_lapse = 0.01
    reference_velocity = 10.0
    brake_heating_sensitivity = 0.02
    frictional_heating_coefficient = 0.5
    thermal_cooling_rate = 0.1
    ambient_temperature = 20.0
    track_slope_amplitude = 0.02
    track_wavenumber = 0.05
    track_slope_phase = 0.0
    headwind_amplitude = 3.0
    headwind_wavenumber = 0.1
    headwind_phase = 0.5

    for point in input_data:
        t = point['t']
        v = point['v']
        brake_temperature = point['brake_temperature']
        cart_position = point['cart_position']
        dv_dt = -(drag_coefficient / cart_mass) * (1 + air_density_lapse * (v - reference_velocity)) * (v + headwind_amplitude * sin(headwind_wavenumber * cart_position + headwind_phase)) * Abs(v + headwind_amplitude * sin(headwind_wavenumber * cart_position + headwind_phase)) - (rolling_resistance_coefficient * gravity) * tanh(v / velocity_scale) * (1 + brake_heating_sensitivity * brake_temperature) + (track_slope_amplitude * gravity) * sin(track_wavenumber * cart_position + track_slope_phase)
        predictions.append({'dv_dt': float(dv_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_classical_mechanics_0_000_gen5_20260728_104929 Reference Law

Target: `dv_dt`

Input variables: `t`, `v`, `brake_temperature`, `cart_position`

Reference expression:

```text
dv_dt = -(drag_coefficient / cart_mass) * (1 + air_density_lapse * (v - reference_velocity)) * (v + headwind_amplitude * sin(headwind_wavenumber * cart_position + headwind_phase)) * Abs(v + headwind_amplitude * sin(headwind_wavenumber * cart_position + headwind_phase)) - (rolling_resistance_coefficient * gravity) * tanh(v / velocity_scale) * (1 + brake_heating_sensitivity * brake_temperature) + (track_slope_amplitude * gravity) * sin(track_wavenumber * cart_position + track_slope_phase)
```

Fixed parameters: drag_coefficient=0.3, cart_mass=100, rolling_resistance_coefficient=0.01, gravity=9.81, velocity_scale=0.5, air_density_lapse=0.01, reference_velocity=10, brake_heating_sensitivity=0.02, frictional_heating_coefficient=0.5, thermal_cooling_rate=0.1, ambient_temperature=20, track_slope_amplitude=0.02, track_wavenumber=0.05, track_slope_phase=0, headwind_amplitude=3, headwind_wavenumber=0.1, headwind_phase=0.5.
EOL
