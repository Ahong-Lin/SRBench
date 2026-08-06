#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_007_gen9_20260728_105922

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
    k_autocatalytic = 8.0
    K_zymogen_saturation = 0.1
    k_complex_dissociation = 1.0
    k_maturation = 2.0
    fraction_concerted_activation = 0.3
    k_product_release = 3.0
    k_activation_triggered_release = 1.5
    k_spontaneous_activation = 0.003
    k_rapid_encounter_activation = 4.0
    K_rapid_encounter_zymogen = 0.15

    for point in input_data:
        t = point['t']
        a = point['a']
        c_productive = point['c_productive']
        maturation_intermediate = point['maturation_intermediate']
        c_cleaved_product = point['c_cleaved_product']
        da_dt = k_maturation*maturation_intermediate + (fraction_concerted_activation*k_product_release + k_activation_triggered_release)*c_cleaved_product + k_spontaneous_activation*(1 - a - maturation_intermediate - c_productive - c_cleaved_product) + k_rapid_encounter_activation*(a - c_productive - c_cleaved_product)*(1 - a - maturation_intermediate - c_productive - c_cleaved_product)/(K_rapid_encounter_zymogen + (1 - a - maturation_intermediate - c_productive - c_cleaved_product))
        predictions.append({'da_dt': float(da_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_007_gen9_20260728_105922 Reference Law

Target: `da_dt`

Input variables: `t`, `a`, `c_productive`, `maturation_intermediate`, `c_cleaved_product`

Reference expression:

```text
da_dt = k_maturation*maturation_intermediate + (fraction_concerted_activation*k_product_release + k_activation_triggered_release)*c_cleaved_product + k_spontaneous_activation*(1 - a - maturation_intermediate - c_productive - c_cleaved_product) + k_rapid_encounter_activation*(a - c_productive - c_cleaved_product)*(1 - a - maturation_intermediate - c_productive - c_cleaved_product)/(K_rapid_encounter_zymogen + (1 - a - maturation_intermediate - c_productive - c_cleaved_product))
```

Fixed parameters: k_autocatalytic=8, K_zymogen_saturation=0.1, k_complex_dissociation=1, k_maturation=2, fraction_concerted_activation=0.3, k_product_release=3, k_activation_triggered_release=1.5, k_spontaneous_activation=0.003, k_rapid_encounter_activation=4, K_rapid_encounter_zymogen=0.15.
EOL
