#!/bin/bash
# Reference solution for m2_population_ecology_0_003_gen7_20260728_105923

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
    intrinsic_growth_rate_1 = 0.8
    intrinsic_growth_rate_2 = 0.6
    opportunity_capacity = 100.0
    competition_coefficient_12 = 0.6
    competition_coefficient_21 = 0.5
    competition_saturation_strength_12 = 0.5
    direct_interference_max_mortality_rate_12 = 0.3
    direct_interference_half_saturation_abundance_12 = 50.0
    direct_interference_victim_saturation_abundance_12 = 50.0
    direct_interference_response_timescale_12 = 5.0
    nonlethal_interference_maximum_recruitment_suppression_fraction_12 = 0.3
    nonlethal_interference_half_saturation_abundance_12 = 50.0
    nonlethal_interference_victim_saturation_abundance_12 = 50.0
    nonlethal_interference_response_timescale_12 = 5.0
    nonlethal_stress_lethal_susceptibility_strength_12 = 3.0

    for point in input_data:
        t = point['t']
        N1 = point['N1']
        N2 = point['N2']
        direct_interference_pressure_12 = point['direct_interference_pressure_12']
        nonlethal_interference_pressure_12 = point['nonlethal_interference_pressure_12']
        dN1_dt = intrinsic_growth_rate_1*N1*(1 - (N1 + competition_coefficient_12*N2/(1 + competition_saturation_strength_12*N2/opportunity_capacity))/opportunity_capacity) - direct_interference_max_mortality_rate_12*N1*direct_interference_pressure_12*(1 + nonlethal_stress_lethal_susceptibility_strength_12*nonlethal_interference_pressure_12)/(1 + nonlethal_stress_lethal_susceptibility_strength_12*direct_interference_pressure_12*nonlethal_interference_pressure_12) - intrinsic_growth_rate_1*nonlethal_interference_maximum_recruitment_suppression_fraction_12*N1*nonlethal_interference_pressure_12
        predictions.append({'dN1_dt': float(dN1_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_003_gen7_20260728_105923 Reference Law

Target: `dN1_dt`

Input variables: `t`, `N1`, `N2`, `direct_interference_pressure_12`, `nonlethal_interference_pressure_12`

Reference expression:

```text
dN1_dt = intrinsic_growth_rate_1*N1*(1 - (N1 + competition_coefficient_12*N2/(1 + competition_saturation_strength_12*N2/opportunity_capacity))/opportunity_capacity) - direct_interference_max_mortality_rate_12*N1*direct_interference_pressure_12*(1 + nonlethal_stress_lethal_susceptibility_strength_12*nonlethal_interference_pressure_12)/(1 + nonlethal_stress_lethal_susceptibility_strength_12*direct_interference_pressure_12*nonlethal_interference_pressure_12) - intrinsic_growth_rate_1*nonlethal_interference_maximum_recruitment_suppression_fraction_12*N1*nonlethal_interference_pressure_12
```

Fixed parameters: intrinsic_growth_rate_1=0.8, intrinsic_growth_rate_2=0.6, opportunity_capacity=100, competition_coefficient_12=0.6, competition_coefficient_21=0.5, competition_saturation_strength_12=0.5, direct_interference_max_mortality_rate_12=0.3, direct_interference_half_saturation_abundance_12=50, direct_interference_victim_saturation_abundance_12=50, direct_interference_response_timescale_12=5, nonlethal_interference_maximum_recruitment_suppression_fraction_12=0.3, nonlethal_interference_half_saturation_abundance_12=50, nonlethal_interference_victim_saturation_abundance_12=50, nonlethal_interference_response_timescale_12=5, nonlethal_stress_lethal_susceptibility_strength_12=3.
EOL
