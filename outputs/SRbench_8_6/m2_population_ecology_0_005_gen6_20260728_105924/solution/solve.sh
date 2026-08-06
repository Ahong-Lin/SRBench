#!/bin/bash
# Reference solution for m2_population_ecology_0_005_gen6_20260728_105924

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
    departure_rate = 1.0
    distance_loss_rate = 0.1
    distance_hazard_shape = 1.5
    landscape_loss_multiplier = 1.0
    destination_area_multiplier = 1.0
    destination_edge_permeability_multiplier = 1.0
    destination_encounter_scale = 5.0
    spatial_dilution_exponent = 2.0
    cue_guided_reorientation_probability = 0.5
    destination_cue_decay_scale = 5.0

    for point in input_data:
        d = point['d']
        m = departure_rate*exp(-landscape_loss_multiplier*(distance_loss_rate*d)**distance_hazard_shape)*(destination_area_multiplier*destination_edge_permeability_multiplier)/(destination_area_multiplier*destination_edge_permeability_multiplier + (d/destination_encounter_scale)**spatial_dilution_exponent)*(1 + cue_guided_reorientation_probability*exp(-d/destination_cue_decay_scale)*(1 - (destination_area_multiplier*destination_edge_permeability_multiplier)/(destination_area_multiplier*destination_edge_permeability_multiplier + (d/destination_encounter_scale)**spatial_dilution_exponent)))
        predictions.append({'m': float(m)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_005_gen6_20260728_105924 Reference Law

Target: `m`

Input variables: `d`

Reference expression:

```text
m = departure_rate*exp(-landscape_loss_multiplier*(distance_loss_rate*d)**distance_hazard_shape)*(destination_area_multiplier*destination_edge_permeability_multiplier)/(destination_area_multiplier*destination_edge_permeability_multiplier + (d/destination_encounter_scale)**spatial_dilution_exponent)*(1 + cue_guided_reorientation_probability*exp(-d/destination_cue_decay_scale)*(1 - (destination_area_multiplier*destination_edge_permeability_multiplier)/(destination_area_multiplier*destination_edge_permeability_multiplier + (d/destination_encounter_scale)**spatial_dilution_exponent)))
```

Fixed parameters: departure_rate=1, distance_loss_rate=0.1, distance_hazard_shape=1.5, landscape_loss_multiplier=1, destination_area_multiplier=1, destination_edge_permeability_multiplier=1, destination_encounter_scale=5, spatial_dilution_exponent=2, cue_guided_reorientation_probability=0.5, destination_cue_decay_scale=5.
EOL
