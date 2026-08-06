#!/bin/bash
# Reference solution for m2_population_ecology_0_000_gen5_20260728_105922

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
    intrinsic_growth_rate = 0.5
    carrying_capacity = 80.0
    crowding_exponent = 2.0
    crowding_relaxation_rate = 1.0
    baseline_mortality_rate = 0.1
    crowding_mortality_fraction = 0.5
    resource_deficit_mortality_rate = 0.8
    resource_deficit_exponent = 1.5

    for point in input_data:
        t = point['t']
        N = point['N']
        crowding_load = point['crowding_load']
        dN_dt = N*((intrinsic_growth_rate + baseline_mortality_rate)/(1 + (intrinsic_growth_rate*(1 - crowding_mortality_fraction)/(baseline_mortality_rate + crowding_mortality_fraction*intrinsic_growth_rate))*(crowding_load/carrying_capacity)**crowding_exponent) - baseline_mortality_rate - crowding_mortality_fraction*intrinsic_growth_rate*(crowding_load/carrying_capacity)**crowding_exponent) - resource_deficit_mortality_rate*N*((N/carrying_capacity - 1 + Abs(N/carrying_capacity - 1))/2)**resource_deficit_exponent
        predictions.append({'dN_dt': float(dN_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_000_gen5_20260728_105922 Reference Law

Target: `dN_dt`

Input variables: `t`, `N`, `crowding_load`

Reference expression:

```text
dN_dt = N*((intrinsic_growth_rate + baseline_mortality_rate)/(1 + (intrinsic_growth_rate*(1 - crowding_mortality_fraction)/(baseline_mortality_rate + crowding_mortality_fraction*intrinsic_growth_rate))*(crowding_load/carrying_capacity)**crowding_exponent) - baseline_mortality_rate - crowding_mortality_fraction*intrinsic_growth_rate*(crowding_load/carrying_capacity)**crowding_exponent) - resource_deficit_mortality_rate*N*((N/carrying_capacity - 1 + Abs(N/carrying_capacity - 1))/2)**resource_deficit_exponent
```

Fixed parameters: intrinsic_growth_rate=0.5, carrying_capacity=80, crowding_exponent=2, crowding_relaxation_rate=1, baseline_mortality_rate=0.1, crowding_mortality_fraction=0.5, resource_deficit_mortality_rate=0.8, resource_deficit_exponent=1.5.
EOL
