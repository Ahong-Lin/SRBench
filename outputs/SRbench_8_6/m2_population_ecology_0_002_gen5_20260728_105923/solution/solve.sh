#!/bin/bash
# Reference solution for m2_population_ecology_0_002_gen5_20260728_105923

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
    attack_rate = 0.5
    handling_time = 0.02
    handling_activation_temperature = 6000.0
    prey_detection_half_saturation = 20.0
    group_defense_pursuit_time = 0.005
    group_defense_half_saturation = 50.0
    predator_confusion_half_saturation = 100.0
    predator_confusion_exponent = 2.5
    attack_activation_temperature = 4000.0

    for point in input_data:
        N = point['N']
        trial_temperature = point['trial_temperature']
        C = attack_rate*N**2/(prey_detection_half_saturation + N + attack_rate*handling_time*exp(handling_activation_temperature*(293 - trial_temperature)/(293*trial_temperature))*N**2 + attack_rate*group_defense_pursuit_time*N**3/(group_defense_half_saturation + N) + (prey_detection_half_saturation + N)*(N/predator_confusion_half_saturation)**predator_confusion_exponent + (prey_detection_half_saturation + N)*(1 + (N/predator_confusion_half_saturation)**predator_confusion_exponent)*(exp(attack_activation_temperature*(293 - trial_temperature)/(293*trial_temperature)) - 1))
        predictions.append({'C': float(C)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_population_ecology_0_002_gen5_20260728_105923 Reference Law

Target: `C`

Input variables: `N`, `trial_temperature`

Reference expression:

```text
C = attack_rate*N**2/(prey_detection_half_saturation + N + attack_rate*handling_time*exp(handling_activation_temperature*(293 - trial_temperature)/(293*trial_temperature))*N**2 + attack_rate*group_defense_pursuit_time*N**3/(group_defense_half_saturation + N) + (prey_detection_half_saturation + N)*(N/predator_confusion_half_saturation)**predator_confusion_exponent + (prey_detection_half_saturation + N)*(1 + (N/predator_confusion_half_saturation)**predator_confusion_exponent)*(exp(attack_activation_temperature*(293 - trial_temperature)/(293*trial_temperature)) - 1))
```

Fixed parameters: attack_rate=0.5, handling_time=0.02, handling_activation_temperature=6000, prey_detection_half_saturation=20, group_defense_pursuit_time=0.005, group_defense_half_saturation=50, predator_confusion_half_saturation=100, predator_confusion_exponent=2.5, attack_activation_temperature=4000.
EOL
