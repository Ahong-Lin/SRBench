#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_008_gen8_20260728_105922

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
    Vmax_first = 1.0
    Km_first = 0.5
    Ki_inhibition = 0.5
    hill_coefficient = 4.0
    Vmax_second = 0.5
    Km_second = 0.3
    Vmax_third = 0.4
    Km_third = 0.2
    Vmax_second_reverse = 0.05
    Km_second_reverse = 0.5
    allosteric_switch_rate = 1.0
    Vmax_first_inhibited = 0.05
    Km_first_inhibited = 1.0
    Ki_first_product = 0.5
    Vmax_first_reverse = 0.05
    Vmax_first_reverse_inhibited = 0.005
    Ki_second_substrate_inhibition = 0.2

    for point in input_data:
        t = point['t']
        S = point['S']
        X = point['X']
        I = point['I']
        active_first_fraction = point['active_first_fraction']
        dX_dt = Vmax_first*active_first_fraction*S/(Km_first*(1 + X/Ki_first_product) + S) + Vmax_first_inhibited*(1 - active_first_fraction)*S/(Km_first_inhibited*(1 + X/Ki_first_product) + S) - (Vmax_second*X/Km_second - Vmax_second_reverse*I/Km_second_reverse)/(1 + X/Km_second + I/Km_second_reverse + X**2/(Km_second*Ki_second_substrate_inhibition)) - Vmax_first_reverse*active_first_fraction*(X/Ki_first_product)/(1 + S/Km_first + X/Ki_first_product) - Vmax_first_reverse_inhibited*(1 - active_first_fraction)*(X/Ki_first_product)/(1 + S/Km_first_inhibited + X/Ki_first_product)
        predictions.append({'dX_dt': float(dX_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_008_gen8_20260728_105922 Reference Law

Target: `dX_dt`

Input variables: `t`, `S`, `X`, `I`, `active_first_fraction`

Reference expression:

```text
dX_dt = Vmax_first*active_first_fraction*S/(Km_first*(1 + X/Ki_first_product) + S) + Vmax_first_inhibited*(1 - active_first_fraction)*S/(Km_first_inhibited*(1 + X/Ki_first_product) + S) - (Vmax_second*X/Km_second - Vmax_second_reverse*I/Km_second_reverse)/(1 + X/Km_second + I/Km_second_reverse + X**2/(Km_second*Ki_second_substrate_inhibition)) - Vmax_first_reverse*active_first_fraction*(X/Ki_first_product)/(1 + S/Km_first + X/Ki_first_product) - Vmax_first_reverse_inhibited*(1 - active_first_fraction)*(X/Ki_first_product)/(1 + S/Km_first_inhibited + X/Ki_first_product)
```

Fixed parameters: Vmax_first=1, Km_first=0.5, Ki_inhibition=0.5, hill_coefficient=4, Vmax_second=0.5, Km_second=0.3, Vmax_third=0.4, Km_third=0.2, Vmax_second_reverse=0.05, Km_second_reverse=0.5, allosteric_switch_rate=1, Vmax_first_inhibited=0.05, Km_first_inhibited=1, Ki_first_product=0.5, Vmax_first_reverse=0.05, Vmax_first_reverse_inhibited=0.005, Ki_second_substrate_inhibition=0.2.
EOL
