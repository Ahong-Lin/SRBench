#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_001_gen5_20260728_105921

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
    k_cat_dim = 1.0
    K_dimer = 10.0
    K_tetramer_inhib = 0.5
    f_tetramer_activity = 0.3
    tetramer_substrate_affinity_ratio = 10.0

    for point in input_data:
        E_T = point['E_T']
        substrate_bound_fraction = point['substrate_bound_fraction']
        v_dim = k_cat_dim*(4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))/8*(substrate_bound_fraction*2/(1 + sqrt(1 + (4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))*(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)**2/(K_tetramer_inhib*tetramer_substrate_affinity_ratio**2))) + f_tetramer_activity*substrate_bound_fraction/(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)*(1 - 2/(1 + sqrt(1 + (4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))*(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)**2/(K_tetramer_inhib*tetramer_substrate_affinity_ratio**2)))))
        predictions.append({'v_dim': float(v_dim)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_001_gen5_20260728_105921 Reference Law

Target: `v_dim`

Input variables: `E_T`, `substrate_bound_fraction`

Reference expression:

```text
v_dim = k_cat_dim*(4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))/8*(substrate_bound_fraction*2/(1 + sqrt(1 + (4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))*(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)**2/(K_tetramer_inhib*tetramer_substrate_affinity_ratio**2))) + f_tetramer_activity*substrate_bound_fraction/(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)*(1 - 2/(1 + sqrt(1 + (4*E_T + K_dimer - sqrt(K_dimer**2 + 8*K_dimer*E_T))*(tetramer_substrate_affinity_ratio*(1 - substrate_bound_fraction) + substrate_bound_fraction)**2/(K_tetramer_inhib*tetramer_substrate_affinity_ratio**2)))))
```

Fixed parameters: k_cat_dim=1, K_dimer=10, K_tetramer_inhib=0.5, f_tetramer_activity=0.3, tetramer_substrate_affinity_ratio=10.
EOL
