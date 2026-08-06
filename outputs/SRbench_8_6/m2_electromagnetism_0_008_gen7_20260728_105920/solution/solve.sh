#!/bin/bash
# Reference solution for m2_electromagnetism_0_008_gen7_20260728_105920

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
    inductance = 0.01
    capacitance = 1e-05
    series_resistance = 0.1
    nonlinear_charge_scale = 0.0005
    radiation_reaction_time = 1e-06
    inductor_saturation_current = 0.5
    air_core_inductance_fraction = 0.5
    core_magnetic_relaxation_time = 0.0005
    dielectric_relaxation_capacitance = 1e-05
    dielectric_relaxation_time = 0.005

    for point in input_data:
        t = point['t']
        Q = point['Q']
        I = point['I']
        core_flux_linkage = point['core_flux_linkage']
        dielectric_memory_charge = point['dielectric_memory_charge']
        dI_dt = -(Q/capacitance + series_resistance*I + Q**3/(capacitance*nonlinear_charge_scale**2) + (Q - dielectric_memory_charge)/dielectric_relaxation_capacitance + radiation_reaction_time*(I*(1 + 3*Q**2/nonlinear_charge_scale**2)/capacitance + (I - (Q - dielectric_memory_charge)/dielectric_relaxation_time)/dielectric_relaxation_capacitance) + (inductance*(1 - air_core_inductance_fraction)*inductor_saturation_current*log(I/inductor_saturation_current + sqrt(1 + I**2/inductor_saturation_current**2)) - core_flux_linkage)/core_magnetic_relaxation_time)/(inductance*air_core_inductance_fraction)
        predictions.append({'dI_dt': float(dI_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_008_gen7_20260728_105920 Reference Law

Target: `dI_dt`

Input variables: `t`, `Q`, `I`, `core_flux_linkage`, `dielectric_memory_charge`

Reference expression:

```text
dI_dt = -(Q/capacitance + series_resistance*I + Q**3/(capacitance*nonlinear_charge_scale**2) + (Q - dielectric_memory_charge)/dielectric_relaxation_capacitance + radiation_reaction_time*(I*(1 + 3*Q**2/nonlinear_charge_scale**2)/capacitance + (I - (Q - dielectric_memory_charge)/dielectric_relaxation_time)/dielectric_relaxation_capacitance) + (inductance*(1 - air_core_inductance_fraction)*inductor_saturation_current*log(I/inductor_saturation_current + sqrt(1 + I**2/inductor_saturation_current**2)) - core_flux_linkage)/core_magnetic_relaxation_time)/(inductance*air_core_inductance_fraction)
```

Fixed parameters: inductance=0.01, capacitance=1e-05, series_resistance=0.1, nonlinear_charge_scale=0.0005, radiation_reaction_time=1e-06, inductor_saturation_current=0.5, air_core_inductance_fraction=0.5, core_magnetic_relaxation_time=0.0005, dielectric_relaxation_capacitance=1e-05, dielectric_relaxation_time=0.005.
EOL
