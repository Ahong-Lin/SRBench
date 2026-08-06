#!/bin/bash
# Reference solution for m2_population_ecology_0_008_gen5_20260728_105924

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
    omega0 = 10.0
    D_corr = 1.5
    rho_ref = 0.5
    exclusion_strength = 0.9
    exclusion_radius = 3.0

    for point in input_data:
        R = point['R']
        A_rel = point['A_rel']
        habitat_quality_rel = point['habitat_quality_rel']
        C_R = omega0*A_rel*habitat_quality_rel*(R**D_corr - exclusion_strength*exclusion_radius**D_corr*(1 - exp(-(R/exclusion_radius)**D_corr))) + pi*rho_ref*A_rel*R**2 - pi*rho_ref*A_rel*exclusion_strength*exclusion_radius**2*(1 - exp(-(R/exclusion_radius)**2))
        predictions.append({'C_R': float(C_R)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_008_gen5_20260728_105924 Reference Law

Target: `C_R`

Input variables: `R`, `A_rel`, `habitat_quality_rel`

Reference expression:

```text
C_R = omega0*A_rel*habitat_quality_rel*(R**D_corr - exclusion_strength*exclusion_radius**D_corr*(1 - exp(-(R/exclusion_radius)**D_corr))) + pi*rho_ref*A_rel*R**2 - pi*rho_ref*A_rel*exclusion_strength*exclusion_radius**2*(1 - exp(-(R/exclusion_radius)**2))
```

Fixed parameters: omega0=10, D_corr=1.5, rho_ref=0.5, exclusion_strength=0.9, exclusion_radius=3.
EOL
