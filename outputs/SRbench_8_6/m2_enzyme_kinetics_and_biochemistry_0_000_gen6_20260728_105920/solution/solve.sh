#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_000_gen6_20260728_105920

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
    kcat = 100.0
    enzyme_total = 0.1
    K_m = 50.0
    active_enzyme_fraction = 0.8
    kcat_allosteric = 50.0
    K_allosteric = 30.0
    allosteric_hill_coefficient = 2.0
    catalytic_acid_pKa = 5.0
    catalytic_base_pKa = 9.0
    binding_site_pKa = 6.0

    for point in input_data:
        S = point['S']
        pH = point['pH']
        v0 = (1 + 10**(catalytic_acid_pKa - 7) + 10**(7 - catalytic_base_pKa))/(1 + 10**(catalytic_acid_pKa - pH) + 10**(pH - catalytic_base_pKa))*(kcat + kcat_allosteric*((S - active_enzyme_fraction*enzyme_total - K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) + sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2)**allosteric_hill_coefficient/(K_allosteric**allosteric_hill_coefficient + ((S - active_enzyme_fraction*enzyme_total - K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) + sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2)**allosteric_hill_coefficient))*(active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) - sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2
        predictions.append({'v0': float(v0)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_000_gen6_20260728_105920 Reference Law

Target: `v0`

Input variables: `S`, `pH`

Reference expression:

```text
v0 = (1 + 10**(catalytic_acid_pKa - 7) + 10**(7 - catalytic_base_pKa))/(1 + 10**(catalytic_acid_pKa - pH) + 10**(pH - catalytic_base_pKa))*(kcat + kcat_allosteric*((S - active_enzyme_fraction*enzyme_total - K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) + sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2)**allosteric_hill_coefficient/(K_allosteric**allosteric_hill_coefficient + ((S - active_enzyme_fraction*enzyme_total - K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) + sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2)**allosteric_hill_coefficient))*(active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)) - sqrt((active_enzyme_fraction*enzyme_total + S + K_m*(1 + 10**(binding_site_pKa - pH))/(1 + 10**(binding_site_pKa - 7)))**2 - 4*active_enzyme_fraction*enzyme_total*S))/2
```

Fixed parameters: kcat=100, enzyme_total=0.1, K_m=50, active_enzyme_fraction=0.8, kcat_allosteric=50, K_allosteric=30, allosteric_hill_coefficient=2, catalytic_acid_pKa=5, catalytic_base_pKa=9, binding_site_pKa=6.
EOL
