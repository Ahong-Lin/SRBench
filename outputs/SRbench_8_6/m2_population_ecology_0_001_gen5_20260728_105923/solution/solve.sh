#!/bin/bash
# Reference solution for m2_population_ecology_0_001_gen5_20260728_105923

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
    intrinsic_growth_rate = 1.0
    allee_threshold = 10.0
    carrying_capacity = 200.0
    unmated_loss_rate = 0.2
    mate_encounter_scale = 100.0
    mate_encounter_memory_time = 5.0
    mate_encounter_dispersion_shape = 3.0
    mating_status_relaxation_time = 3.0

    for point in input_data:
        t = point['t']
        N = point['N']
        experienced_mate_abundance = point['experienced_mate_abundance']
        unmated_fraction = point['unmated_fraction']
        mating_type_fraction = point['mating_type_fraction']
        dN_dt = intrinsic_growth_rate*N*(4*mating_type_fraction*(1 - mating_type_fraction)*(N/allee_threshold - 1) + (1 - 4*mating_type_fraction*(1 - mating_type_fraction))*(N/carrying_capacity - 1))*(1 - N/carrying_capacity) - unmated_loss_rate*N*unmated_fraction
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_001_gen5_20260728_105923 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`, `experienced_mate_abundance`, `unmated_fraction`, `mating_type_fraction`

Reference expression:

```text
dN_dt = intrinsic_growth_rate*N*(4*mating_type_fraction*(1 - mating_type_fraction)*(N/allee_threshold - 1) + (1 - 4*mating_type_fraction*(1 - mating_type_fraction))*(N/carrying_capacity - 1))*(1 - N/carrying_capacity) - unmated_loss_rate*N*unmated_fraction
```

Fixed parameters: intrinsic_growth_rate=1, allee_threshold=10, carrying_capacity=200, unmated_loss_rate=0.2, mate_encounter_scale=100, mate_encounter_memory_time=5, mate_encounter_dispersion_shape=3, mating_status_relaxation_time=3.
EOL
