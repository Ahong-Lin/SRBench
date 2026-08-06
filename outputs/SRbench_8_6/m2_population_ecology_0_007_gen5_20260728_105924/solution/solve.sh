#!/bin/bash
# Reference solution for m2_population_ecology_0_007_gen5_20260728_105924

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
    rescue_max_fraction = 0.2
    rescue_pressure_scale = 0.5
    spatial_isolation_strength = 1.5
    effective_donor_degree = 8.0
    donor_degree_dispersion = 1.0

    for point in input_data:
        c = point['c']
        e = point['e']
        immigration_rate = point['immigration_rate']
        suitable_habitat_fraction = point['suitable_habitat_fraction']
        p_star = (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c) + rescue_max_fraction*(suitable_habitat_fraction - (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*tanh((c*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c)) + immigration_rate)/rescue_pressure_scale) - spatial_isolation_strength*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*(suitable_habitat_fraction - (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*(1 + effective_donor_degree*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))/donor_degree_dispersion)**(-donor_degree_dispersion)
        predictions.append({'p_star': float(p_star)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_007_gen5_20260728_105924 Reference Law

Target: `p_star`

Input variables: `c`, `e`, `immigration_rate`, `suitable_habitat_fraction`

Reference expression:

```text
p_star = (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c) + rescue_max_fraction*(suitable_habitat_fraction - (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*tanh((c*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c)) + immigration_rate)/rescue_pressure_scale) - spatial_isolation_strength*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*(suitable_habitat_fraction - (c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))*(1 + effective_donor_degree*((c*suitable_habitat_fraction - e - immigration_rate + sqrt((c*suitable_habitat_fraction - e - immigration_rate)**2 + 4*c*immigration_rate*suitable_habitat_fraction))/(2*c))/donor_degree_dispersion)**(-donor_degree_dispersion)
```

Fixed parameters: rescue_max_fraction=0.2, rescue_pressure_scale=0.5, spatial_isolation_strength=1.5, effective_donor_degree=8, donor_degree_dispersion=1.
EOL
