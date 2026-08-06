#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_004_gen5_20260728_105921

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
    E_total = 0.01
    kcat_forward = 100.0
    kcat_reverse = 50.0
    K_A = 1.0
    K_B = 1.0
    K_P = 1.0
    K_Q = 1.0
    alpha_AB = 1.0
    alpha_AQ = 2.0
    alpha_BP = 2.0
    K_A_inhibitory = 5.0
    K_B_inhibitory = 5.0

    for point in input_data:
        A = point['A']
        B = point['B']
        P = point['P']
        Q = point['Q']
        J_net = E_total*(kcat_forward*A*B/(alpha_AB*K_A*K_B) - kcat_reverse*P*Q/(K_P*K_Q))/(1 + A/K_A + B/K_B + A*B/(alpha_AB*K_A*K_B) + P/K_P + Q/K_Q + P*Q/(K_P*K_Q) + A*Q/(alpha_AQ*K_A*K_Q) + B*P/(alpha_BP*K_B*K_P) + A**2/(K_A*K_A_inhibitory) + B**2/(K_B*K_B_inhibitory))
        predictions.append({'J_net': float(J_net)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_004_gen5_20260728_105921 Reference Law

Target: `J_net`

Input variables: `A`, `B`, `P`, `Q`

Reference expression:

```text
J_net = E_total*(kcat_forward*A*B/(alpha_AB*K_A*K_B) - kcat_reverse*P*Q/(K_P*K_Q))/(1 + A/K_A + B/K_B + A*B/(alpha_AB*K_A*K_B) + P/K_P + Q/K_Q + P*Q/(K_P*K_Q) + A*Q/(alpha_AQ*K_A*K_Q) + B*P/(alpha_BP*K_B*K_P) + A**2/(K_A*K_A_inhibitory) + B**2/(K_B*K_B_inhibitory))
```

Fixed parameters: E_total=0.01, kcat_forward=100, kcat_reverse=50, K_A=1, K_B=1, K_P=1, K_Q=1, alpha_AB=1, alpha_AQ=2, alpha_BP=2, K_A_inhibitory=5, K_B_inhibitory=5.
EOL
