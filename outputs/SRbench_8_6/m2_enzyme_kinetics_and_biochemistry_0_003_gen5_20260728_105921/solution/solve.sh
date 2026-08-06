#!/bin/bash
# Reference solution for m2_enzyme_kinetics_and_biochemistry_0_003_gen5_20260728_105921

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
    k_turn_active = 100.0
    pKa_deprotonated_site = 5.0
    pKa_protonated_site = 8.0
    joint_misprotonation_weight_factor = 0.5
    turnover_activation_enthalpy_over_gas_constant = 6000.0
    deprotonated_site_ionization_enthalpy_over_gas_constant = 500.0
    protonated_site_ionization_enthalpy_over_gas_constant = 3000.0
    joint_misprotonation_coupling_enthalpy_over_gas_constant = 1000.0
    turnover_activation_heat_capacity_over_gas_constant = -100.0
    deprotonated_site_ionic_strength_pKa_sensitivity = 1.0
    protonated_site_ionic_strength_pKa_sensitivity = 0.5
    joint_misprotonation_ionic_strength_log_weight_sensitivity = 1.0
    ionic_strength_screening_coefficient = 1.5

    for point in input_data:
        pH = point['pH']
        temperature = point['temperature']
        ionic_strength = point['ionic_strength']
        k_turn = k_turn_active*(temperature/298)*exp(-turnover_activation_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature))*exp(turnover_activation_heat_capacity_over_gas_constant*(log(temperature/298) - (temperature - 298)/temperature))/(1 + 10**(pKa_deprotonated_site + deprotonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) + deprotonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))) - pH) + 10**(pH - pKa_protonated_site - protonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) - protonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10)))) + joint_misprotonation_weight_factor*exp(-joint_misprotonation_coupling_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature))*exp(joint_misprotonation_ionic_strength_log_weight_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))))*10**(pKa_deprotonated_site + deprotonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) + deprotonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))) - pH)*10**(pH - pKa_protonated_site - protonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) - protonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10)))))
        predictions.append({'k_turn': float(k_turn)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_enzyme_kinetics_and_biochemistry_0_003_gen5_20260728_105921 Reference Law

Target: `k_turn`

Input variables: `pH`, `temperature`, `ionic_strength`

Reference expression:

```text
k_turn = k_turn_active*(temperature/298)*exp(-turnover_activation_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature))*exp(turnover_activation_heat_capacity_over_gas_constant*(log(temperature/298) - (temperature - 298)/temperature))/(1 + 10**(pKa_deprotonated_site + deprotonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) + deprotonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))) - pH) + 10**(pH - pKa_protonated_site - protonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) - protonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10)))) + joint_misprotonation_weight_factor*exp(-joint_misprotonation_coupling_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature))*exp(joint_misprotonation_ionic_strength_log_weight_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))))*10**(pKa_deprotonated_site + deprotonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) + deprotonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10))) - pH)*10**(pH - pKa_protonated_site - protonated_site_ionization_enthalpy_over_gas_constant*(298 - temperature)/(298*temperature*log(10)) - protonated_site_ionic_strength_pKa_sensitivity*(sqrt(ionic_strength)/(1 + ionic_strength_screening_coefficient*sqrt(ionic_strength)) - (1/sqrt(10))/(1 + ionic_strength_screening_coefficient/sqrt(10)))))
```

Fixed parameters: k_turn_active=100, pKa_deprotonated_site=5, pKa_protonated_site=8, joint_misprotonation_weight_factor=0.5, turnover_activation_enthalpy_over_gas_constant=6000, deprotonated_site_ionization_enthalpy_over_gas_constant=500, protonated_site_ionization_enthalpy_over_gas_constant=3000, joint_misprotonation_coupling_enthalpy_over_gas_constant=1000, turnover_activation_heat_capacity_over_gas_constant=-100, deprotonated_site_ionic_strength_pKa_sensitivity=1, protonated_site_ionic_strength_pKa_sensitivity=0.5, joint_misprotonation_ionic_strength_log_weight_sensitivity=1, ionic_strength_screening_coefficient=1.5.
EOL
