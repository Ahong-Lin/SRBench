#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_002_gen7_20260728_105921

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
    Vmax = 100.0
    Km = 50.0
    Ki = 300.0
    Ki3 = 300.0
    Ki4 = 300.0
    Ki5 = 300.0
    Ki6 = 300.0
    Ki7 = 300.0
    residual_activity_fraction = 0.2
    crowding_activity_decay = 1.0

    for point in input_data:
        S = point['S']
        v_subinh = Vmax*(S + residual_activity_fraction*(S**2/Ki + exp(-crowding_activity_decay)*S**3/(Ki*Ki3) + exp(-2*crowding_activity_decay)*S**4/(Ki*Ki3*Ki4) + exp(-3*crowding_activity_decay)*S**5/(Ki*Ki3*Ki4*Ki5) + exp(-4*crowding_activity_decay)*S**6/(Ki*Ki3*Ki4*Ki5*Ki6) + exp(-5*crowding_activity_decay)*S**7/(Ki*Ki3*Ki4*Ki5*Ki6*Ki7)))/(Km + S + S**2/Ki + S**3/(Ki*Ki3) + S**4/(Ki*Ki3*Ki4) + S**5/(Ki*Ki3*Ki4*Ki5) + S**6/(Ki*Ki3*Ki4*Ki5*Ki6) + S**7/(Ki*Ki3*Ki4*Ki5*Ki6*Ki7))
        predictions.append({'v_subinh': float(v_subinh)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_002_gen7_20260728_105921 Reference Law

Target: `v_subinh`

Input variables: `S`

Reference expression:

```text
v_subinh = Vmax*(S + residual_activity_fraction*(S**2/Ki + exp(-crowding_activity_decay)*S**3/(Ki*Ki3) + exp(-2*crowding_activity_decay)*S**4/(Ki*Ki3*Ki4) + exp(-3*crowding_activity_decay)*S**5/(Ki*Ki3*Ki4*Ki5) + exp(-4*crowding_activity_decay)*S**6/(Ki*Ki3*Ki4*Ki5*Ki6) + exp(-5*crowding_activity_decay)*S**7/(Ki*Ki3*Ki4*Ki5*Ki6*Ki7)))/(Km + S + S**2/Ki + S**3/(Ki*Ki3) + S**4/(Ki*Ki3*Ki4) + S**5/(Ki*Ki3*Ki4*Ki5) + S**6/(Ki*Ki3*Ki4*Ki5*Ki6) + S**7/(Ki*Ki3*Ki4*Ki5*Ki6*Ki7))
```

Fixed parameters: Vmax=100, Km=50, Ki=300, Ki3=300, Ki4=300, Ki5=300, Ki6=300, Ki7=300, residual_activity_fraction=0.2, crowding_activity_decay=1.
EOL
