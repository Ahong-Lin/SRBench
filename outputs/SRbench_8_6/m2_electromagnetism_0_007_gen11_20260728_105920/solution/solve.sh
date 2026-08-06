#!/bin/bash
# Reference solution for m2_electromagnetism_0_007_gen11_20260728_105920

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
    resistance = 1000.0
    capacitance = 1e-05
    leakage_current_scale = 1e-09
    leakage_voltage_scale = 5.0
    capacitance_dc_bias_coefficient = 0.0001
    dielectric_absorption_fraction = 0.01
    dielectric_absorption_relaxation_time = 0.005
    secondary_dielectric_absorption_fraction = 0.005
    secondary_dielectric_absorption_relaxation_time = 0.02
    electrode_injection_saturation_current = 1e-12
    electrode_injection_voltage_scale = 1.0
    fowler_nordheim_current_coefficient = 1e-09
    fowler_nordheim_barrier_voltage = 20.0
    fowler_nordheim_regularization_voltage = 0.1
    resistance_temperature_coefficient = 0.004
    resistor_thermal_capacitance = 0.1
    resistor_thermal_resistance = 100.0
    poole_frenkel_zero_field_conductance = 1e-08
    poole_frenkel_field_enhancement_coefficient = 0.5
    poole_frenkel_regularization_voltage = 0.1
    space_charge_limited_current_coefficient = 1e-09
    space_charge_limited_regularization_voltage = 0.1
    counterelectrode_injection_saturation_current = 1e-11
    counterelectrode_injection_voltage_scale = 3.0
    schottky_emission_current_scale = 1e-06
    schottky_field_enhancement_coefficient = 1.0
    schottky_emission_regularization_voltage = 0.001

    for point in input_data:
        t = point['t']
        V_C = point['V_C']
        dielectric_absorption_voltage = point['dielectric_absorption_voltage']
        secondary_dielectric_absorption_voltage = point['secondary_dielectric_absorption_voltage']
        resistor_temperature_rise = point['resistor_temperature_rise']
        dV_C_dt = -(1 + capacitance_dc_bias_coefficient*V_C**2)*(V_C/(resistance*(1 + resistance_temperature_coefficient*resistor_temperature_rise)) + leakage_current_scale*sinh(V_C/leakage_voltage_scale) + capacitance*dielectric_absorption_fraction*(V_C - dielectric_absorption_voltage)/dielectric_absorption_relaxation_time + capacitance*secondary_dielectric_absorption_fraction*(V_C - secondary_dielectric_absorption_voltage)/secondary_dielectric_absorption_relaxation_time + electrode_injection_saturation_current*(exp(V_C/electrode_injection_voltage_scale) - 1) + fowler_nordheim_current_coefficient*V_C*sqrt(V_C**2 + fowler_nordheim_regularization_voltage**2)*exp(-fowler_nordheim_barrier_voltage/sqrt(V_C**2 + fowler_nordheim_regularization_voltage**2)) + poole_frenkel_zero_field_conductance*V_C*exp(poole_frenkel_field_enhancement_coefficient*(sqrt(sqrt(V_C**2 + poole_frenkel_regularization_voltage**2)) - sqrt(poole_frenkel_regularization_voltage))) + space_charge_limited_current_coefficient*V_C*(sqrt(V_C**2 + space_charge_limited_regularization_voltage**2) - space_charge_limited_regularization_voltage) + counterelectrode_injection_saturation_current*(1 - exp(-V_C/counterelectrode_injection_voltage_scale)) + schottky_emission_current_scale*V_C/sqrt(V_C**2 + schottky_emission_regularization_voltage**2)*exp(schottky_field_enhancement_coefficient*(sqrt(sqrt(V_C**2 + schottky_emission_regularization_voltage**2)) - sqrt(schottky_emission_regularization_voltage))))/capacitance
        predictions.append({'dV_C_dt': float(dV_C_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_007_gen11_20260728_105920 Reference Law

Target: `dV_C_dt`

Input variables: `t`, `V_C`, `dielectric_absorption_voltage`, `secondary_dielectric_absorption_voltage`, `resistor_temperature_rise`

Reference expression:

```text
dV_C_dt = -(1 + capacitance_dc_bias_coefficient*V_C**2)*(V_C/(resistance*(1 + resistance_temperature_coefficient*resistor_temperature_rise)) + leakage_current_scale*sinh(V_C/leakage_voltage_scale) + capacitance*dielectric_absorption_fraction*(V_C - dielectric_absorption_voltage)/dielectric_absorption_relaxation_time + capacitance*secondary_dielectric_absorption_fraction*(V_C - secondary_dielectric_absorption_voltage)/secondary_dielectric_absorption_relaxation_time + electrode_injection_saturation_current*(exp(V_C/electrode_injection_voltage_scale) - 1) + fowler_nordheim_current_coefficient*V_C*sqrt(V_C**2 + fowler_nordheim_regularization_voltage**2)*exp(-fowler_nordheim_barrier_voltage/sqrt(V_C**2 + fowler_nordheim_regularization_voltage**2)) + poole_frenkel_zero_field_conductance*V_C*exp(poole_frenkel_field_enhancement_coefficient*(sqrt(sqrt(V_C**2 + poole_frenkel_regularization_voltage**2)) - sqrt(poole_frenkel_regularization_voltage))) + space_charge_limited_current_coefficient*V_C*(sqrt(V_C**2 + space_charge_limited_regularization_voltage**2) - space_charge_limited_regularization_voltage) + counterelectrode_injection_saturation_current*(1 - exp(-V_C/counterelectrode_injection_voltage_scale)) + schottky_emission_current_scale*V_C/sqrt(V_C**2 + schottky_emission_regularization_voltage**2)*exp(schottky_field_enhancement_coefficient*(sqrt(sqrt(V_C**2 + schottky_emission_regularization_voltage**2)) - sqrt(schottky_emission_regularization_voltage))))/capacitance
```

Fixed parameters: resistance=1000, capacitance=1e-05, leakage_current_scale=1e-09, leakage_voltage_scale=5, capacitance_dc_bias_coefficient=0.0001, dielectric_absorption_fraction=0.01, dielectric_absorption_relaxation_time=0.005, secondary_dielectric_absorption_fraction=0.005, secondary_dielectric_absorption_relaxation_time=0.02, electrode_injection_saturation_current=1e-12, electrode_injection_voltage_scale=1, fowler_nordheim_current_coefficient=1e-09, fowler_nordheim_barrier_voltage=20, fowler_nordheim_regularization_voltage=0.1, resistance_temperature_coefficient=0.004, resistor_thermal_capacitance=0.1, resistor_thermal_resistance=100, poole_frenkel_zero_field_conductance=1e-08, poole_frenkel_field_enhancement_coefficient=0.5, poole_frenkel_regularization_voltage=0.1, space_charge_limited_current_coefficient=1e-09, space_charge_limited_regularization_voltage=0.1, counterelectrode_injection_saturation_current=1e-11, counterelectrode_injection_voltage_scale=3, schottky_emission_current_scale=1e-06, schottky_field_enhancement_coefficient=1, schottky_emission_regularization_voltage=0.001.
EOL
