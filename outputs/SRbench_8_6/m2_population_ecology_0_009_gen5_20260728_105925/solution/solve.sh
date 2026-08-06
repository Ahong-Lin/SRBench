#!/bin/bash
# Reference solution for m2_population_ecology_0_009_gen5_20260728_105925

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
    intrinsic_growth_rate = 0.6
    carrying_capacity = 1000.0
    harvest_quota = 40.0
    harvest_availability_scale = 200.0
    crowding_relaxation_time = 5.0
    harvest_encounter_dispersion = 2.0
    crowding_saturation_strength = 0.5
    seasonal_growth_amplitude = 0.15
    seasonal_period = 5.0
    seasonal_phase = 0.0

    for point in input_data:
        t = point['t']
        N = point['N']
        crowding_load = point['crowding_load']
        dN_dt = Piecewise((intrinsic_growth_rate*N*(1 - crowding_load/carrying_capacity)/(1 + crowding_saturation_strength*crowding_load/carrying_capacity) - harvest_quota + harvest_quota*(1 + N/(harvest_encounter_dispersion*harvest_availability_scale))**(-harvest_encounter_dispersion) + seasonal_growth_amplitude*intrinsic_growth_rate*N*(1 - crowding_load/carrying_capacity)/(1 + crowding_saturation_strength*crowding_load/carrying_capacity)*cos(2*pi*t/seasonal_period + seasonal_phase), N > 0), (0, True))
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_009_gen5_20260728_105925 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`, `crowding_load`

Reference expression:

```text
dN_dt = Piecewise((intrinsic_growth_rate*N*(1 - crowding_load/carrying_capacity)/(1 + crowding_saturation_strength*crowding_load/carrying_capacity) - harvest_quota + harvest_quota*(1 + N/(harvest_encounter_dispersion*harvest_availability_scale))**(-harvest_encounter_dispersion) + seasonal_growth_amplitude*intrinsic_growth_rate*N*(1 - crowding_load/carrying_capacity)/(1 + crowding_saturation_strength*crowding_load/carrying_capacity)*cos(2*pi*t/seasonal_period + seasonal_phase), N > 0), (0, True))
```

Fixed parameters: intrinsic_growth_rate=0.6, carrying_capacity=1000, harvest_quota=40, harvest_availability_scale=200, crowding_relaxation_time=5, harvest_encounter_dispersion=2, crowding_saturation_strength=0.5, seasonal_growth_amplitude=0.15, seasonal_period=5, seasonal_phase=0.
EOL
