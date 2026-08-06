#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_006_gen5_20260728_105922

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
    association_rate = 1.0
    dissociation_rate = 2.0
    closing_rate = 0.5
    opening_rate = 0.1
    mixing_deficit_fraction = 0.5
    mixing_relaxation_rate = 2.0
    mixing_stretch_exponent = 0.8
    gated_closing_rate = 1.0
    conformational_relaxation_rate = 0.5
    conformational_stretch_exponent = 0.7
    cage_rebinding_rate = 1.0
    cage_escape_rate = 10.0
    cage_effective_ligand_concentration = 1.0
    diffusive_encounter_enhancement_fraction = 1.5
    diffusive_boundary_relaxation_rate = 5.0

    for point in input_data:
        t = point['t']
        E = point['E']
        L = point['L']
        C = point['C']
        D = point['D']
        dC_dt = association_rate*E*L - dissociation_rate*C - closing_rate*C + opening_rate*D - mixing_deficit_fraction*association_rate*E*L*exp(-(mixing_relaxation_rate*t)**mixing_stretch_exponent) - gated_closing_rate*C*(1 - exp(-(conformational_relaxation_rate*t)**conformational_stretch_exponent)) + dissociation_rate*C*cage_rebinding_rate*(L + cage_effective_ligand_concentration)/(cage_escape_rate + cage_rebinding_rate*(L + cage_effective_ligand_concentration)) + diffusive_encounter_enhancement_fraction*association_rate*E*L/sqrt(1 + diffusive_boundary_relaxation_rate*t)
        predictions.append({'dC_dt': float(dC_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_006_gen5_20260728_105922 Reference Law

Target: `dC_dt`

Input variables: `t`, `E`, `L`, `C`, `D`

Reference expression:

```text
dC_dt = association_rate*E*L - dissociation_rate*C - closing_rate*C + opening_rate*D - mixing_deficit_fraction*association_rate*E*L*exp(-(mixing_relaxation_rate*t)**mixing_stretch_exponent) - gated_closing_rate*C*(1 - exp(-(conformational_relaxation_rate*t)**conformational_stretch_exponent)) + dissociation_rate*C*cage_rebinding_rate*(L + cage_effective_ligand_concentration)/(cage_escape_rate + cage_rebinding_rate*(L + cage_effective_ligand_concentration)) + diffusive_encounter_enhancement_fraction*association_rate*E*L/sqrt(1 + diffusive_boundary_relaxation_rate*t)
```

Fixed parameters: association_rate=1, dissociation_rate=2, closing_rate=0.5, opening_rate=0.1, mixing_deficit_fraction=0.5, mixing_relaxation_rate=2, mixing_stretch_exponent=0.8, gated_closing_rate=1, conformational_relaxation_rate=0.5, conformational_stretch_exponent=0.7, cage_rebinding_rate=1, cage_escape_rate=10, cage_effective_ligand_concentration=1, diffusive_encounter_enhancement_fraction=1.5, diffusive_boundary_relaxation_rate=5.
EOL
