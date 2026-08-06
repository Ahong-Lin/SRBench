#!/bin/bash
# Reference solution for m2_population_ecology_0_006_gen8_20260728_105924

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
    mean_recruitment_rate = 2.0
    recruitment_seasonality = 0.5
    seasonal_phase = 0.7854
    mortality_rate = 0.3
    immature_mortality_rate = 0.5
    crowding_coefficient = 0.0005
    second_harmonic_recruitment_amplitude = 0.2
    second_harmonic_phase = 1.0472
    maturation_rate = 1.0
    mate_finding_half_saturation_abundance = 20.0
    immature_crowding_coefficient = 0.0005
    recruitment_resource_half_saturation_abundance = 100.0
    maturation_seasonality = 0.3
    maturation_phase = 1.5708
    peak_recruitment_pulse_rate = 3.0
    recruitment_pulse_concentration = 5.0
    recruitment_pulse_phase = 1.5708

    for point in input_data:
        t = point['t']
        N = point['N']
        reproductive_adult_abundance = point['reproductive_adult_abundance']
        dN_dt = reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase)) - immature_mortality_rate*(N - reproductive_adult_abundance) - mortality_rate*reproductive_adult_abundance - immature_crowding_coefficient*N*(N - reproductive_adult_abundance) - crowding_coefficient*N*reproductive_adult_abundance - reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase))*mate_finding_half_saturation_abundance/(reproductive_adult_abundance + mate_finding_half_saturation_abundance) - reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase))*reproductive_adult_abundance*N/((reproductive_adult_abundance + mate_finding_half_saturation_abundance)*(N + recruitment_resource_half_saturation_abundance)) + reproductive_adult_abundance*peak_recruitment_pulse_rate*exp(recruitment_pulse_concentration*(cos(2*pi*t - recruitment_pulse_phase) - 1))*reproductive_adult_abundance*recruitment_resource_half_saturation_abundance/((reproductive_adult_abundance + mate_finding_half_saturation_abundance)*(N + recruitment_resource_half_saturation_abundance))
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_006_gen8_20260728_105924 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`, `reproductive_adult_abundance`

Reference expression:

```text
dN_dt = reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase)) - immature_mortality_rate*(N - reproductive_adult_abundance) - mortality_rate*reproductive_adult_abundance - immature_crowding_coefficient*N*(N - reproductive_adult_abundance) - crowding_coefficient*N*reproductive_adult_abundance - reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase))*mate_finding_half_saturation_abundance/(reproductive_adult_abundance + mate_finding_half_saturation_abundance) - reproductive_adult_abundance*mean_recruitment_rate*(1 + recruitment_seasonality*cos(2*pi*t - seasonal_phase) + second_harmonic_recruitment_amplitude*cos(4*pi*t - second_harmonic_phase))*reproductive_adult_abundance*N/((reproductive_adult_abundance + mate_finding_half_saturation_abundance)*(N + recruitment_resource_half_saturation_abundance)) + reproductive_adult_abundance*peak_recruitment_pulse_rate*exp(recruitment_pulse_concentration*(cos(2*pi*t - recruitment_pulse_phase) - 1))*reproductive_adult_abundance*recruitment_resource_half_saturation_abundance/((reproductive_adult_abundance + mate_finding_half_saturation_abundance)*(N + recruitment_resource_half_saturation_abundance))
```

Fixed parameters: mean_recruitment_rate=2, recruitment_seasonality=0.5, seasonal_phase=0.7854, mortality_rate=0.3, immature_mortality_rate=0.5, crowding_coefficient=0.0005, second_harmonic_recruitment_amplitude=0.2, second_harmonic_phase=1.0472, maturation_rate=1, mate_finding_half_saturation_abundance=20, immature_crowding_coefficient=0.0005, recruitment_resource_half_saturation_abundance=100, maturation_seasonality=0.3, maturation_phase=1.5708, peak_recruitment_pulse_rate=3, recruitment_pulse_concentration=5, recruitment_pulse_phase=1.5708.
EOL
