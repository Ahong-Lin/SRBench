#!/bin/bash
# Reference solution for m2_population_ecology_0_001_gen4_20260728_105923

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
    prey_growth_rate = 1.0
    predation_rate = 0.4
    conversion_efficiency = 0.4
    consumer_death_rate = 0.3
    prey_carrying_capacity = 100.0
    handling_time = 0.3
    interference_coefficient = 0.05
    refuge_fraction = 0.5

    for point in input_data:
        t = point['t']
        R = point['R']
        C = point['C']
        dR_dt = prey_growth_rate * R * (1 - R / prey_carrying_capacity) - predation_rate * R * C / (1 + predation_rate * handling_time * R + predation_rate * handling_time * interference_coefficient * C) - predation_rate * R * C / (1 + predation_rate * handling_time * R + predation_rate * handling_time * interference_coefficient * C) * (refuge_fraction * prey_carrying_capacity / (prey_carrying_capacity + R)) * (-1)
        predictions.append({'dR_dt': float(dR_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_001_gen4_20260728_105923 Reference Law

Target: `dR_dt`

Input variables: `t`, `R`, `C`

Reference expression:

```text
dR_dt = prey_growth_rate * R * (1 - R / prey_carrying_capacity) - predation_rate * R * C / (1 + predation_rate * handling_time * R + predation_rate * handling_time * interference_coefficient * C) - predation_rate * R * C / (1 + predation_rate * handling_time * R + predation_rate * handling_time * interference_coefficient * C) * (refuge_fraction * prey_carrying_capacity / (prey_carrying_capacity + R)) * (-1)
```

Fixed parameters: prey_growth_rate=1, predation_rate=0.4, conversion_efficiency=0.4, consumer_death_rate=0.3, prey_carrying_capacity=100, handling_time=0.3, interference_coefficient=0.05, refuge_fraction=0.5.
EOL
