#!/bin/bash
# Reference solution for m2_population_ecology_0_004_gen5_20260728_105923

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
    offspring_rate = 0.5
    maturation_rate = 0.2
    juvenile_mortality_rate = 0.1
    adult_mortality_rate = 0.05
    maturation_crowding_coefficient = 0.005
    adult_crowding_weight = 1.0
    maturation_resource_turnover_time = 1.0
    maximum_adult_starvation_mortality_rate = 0.1
    adult_starvation_resource_half_saturation = 0.5
    adult_energy_reserve_adjustment_time = 10.0

    for point in input_data:
        t = point['t']
        J = point['J']
        A = point['A']
        maturation_resource_level = point['maturation_resource_level']
        adult_energy_reserve_level = point['adult_energy_reserve_level']
        dA_dt = maturation_rate*J*maturation_resource_level - adult_mortality_rate*A - maximum_adult_starvation_mortality_rate*A/(1 + (adult_energy_reserve_level/adult_starvation_resource_half_saturation)**2)
        predictions.append({'dA_dt': float(dA_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_004_gen5_20260728_105923 Reference Law

Target: `dA_dt`

Input variables: `t`, `J`, `A`, `maturation_resource_level`, `adult_energy_reserve_level`

Reference expression:

```text
dA_dt = maturation_rate*J*maturation_resource_level - adult_mortality_rate*A - maximum_adult_starvation_mortality_rate*A/(1 + (adult_energy_reserve_level/adult_starvation_resource_half_saturation)**2)
```

Fixed parameters: offspring_rate=0.5, maturation_rate=0.2, juvenile_mortality_rate=0.1, adult_mortality_rate=0.05, maturation_crowding_coefficient=0.005, adult_crowding_weight=1, maturation_resource_turnover_time=1, maximum_adult_starvation_mortality_rate=0.1, adult_starvation_resource_half_saturation=0.5, adult_energy_reserve_adjustment_time=10.
EOL
