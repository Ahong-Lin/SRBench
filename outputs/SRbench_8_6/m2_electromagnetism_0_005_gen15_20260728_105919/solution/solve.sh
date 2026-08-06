#!/bin/bash
# Reference solution for m2_electromagnetism_0_005_gen15_20260728_105919

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
    c = 300000000.0
    epsilon_0 = 8.854e-12
    relative_permittivity = 1.0
    relative_permeability = 1.0
    source_width = 0.001
    uniform_ball_profile_fraction = 0.5
    profile_component_width_contrast = 0.1
    magnetic_dipole_length = 0.001
    electric_quadrupole_length = 0.001
    magnetic_quadrupole_length = 0.001
    electric_octupole_length = 0.001
    magnetic_octupole_length = 0.001
    electric_hexadecapole_length = 0.001
    magnetic_hexadecapole_length = 0.001
    electric_dotriacontapole_length = 0.001
    magnetic_dotriacontapole_length = 0.001
    electric_tetrahexacontapole_length = 0.001

    for point in input_data:
        p_0 = point['p_0']
        f = point['f']
        P_rad = ((1 - uniform_ball_profile_fraction)*exp(-relative_permittivity*relative_permeability*(2*pi*f*source_width/c)**2*(1 + uniform_ball_profile_fraction*profile_component_width_contrast)/2) + 3*uniform_ball_profile_fraction*(sin(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)) - sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)*cos(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)))/(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c))**3)**2*(p_0**2*(2*pi*f)**4*relative_permeability*sqrt(relative_permittivity*relative_permeability)/(12*pi*epsilon_0*c**3) + p_0**2*electric_quadrupole_length**2*(2*pi*f)**6*relative_permittivity*relative_permeability**2*sqrt(relative_permittivity*relative_permeability)/(1440*pi*epsilon_0*c**5) + p_0**2*magnetic_dipole_length**2*(2*pi*f)**6*relative_permittivity*relative_permeability**2*sqrt(relative_permittivity*relative_permeability)/(12*pi*epsilon_0*c**5) + p_0**2*electric_octupole_length**4*(2*pi*f)**8*relative_permittivity**2*relative_permeability**3*sqrt(relative_permittivity*relative_permeability)/(3780*pi*epsilon_0*c**7) + p_0**2*magnetic_quadrupole_length**4*(2*pi*f)**8*relative_permittivity**2*relative_permeability**3*sqrt(relative_permittivity*relative_permeability)/(1440*pi*epsilon_0*c**7) + p_0**2*electric_hexadecapole_length**6*(2*pi*f)**10*relative_permittivity**3*relative_permeability**4*sqrt(relative_permittivity*relative_permeability)/(145152*pi*epsilon_0*c**9) + p_0**2*magnetic_octupole_length**6*(2*pi*f)**10*relative_permittivity**3*relative_permeability**4*sqrt(relative_permittivity*relative_permeability)/(3780*pi*epsilon_0*c**9) + p_0**2*electric_dotriacontapole_length**8*(2*pi*f)**12*relative_permittivity**4*relative_permeability**5*sqrt(relative_permittivity*relative_permeability)/(8316000*pi*epsilon_0*c**11) + p_0**2*magnetic_hexadecapole_length**8*(2*pi*f)**12*relative_permittivity**4*relative_permeability**5*sqrt(relative_permittivity*relative_permeability)/(145152*pi*epsilon_0*c**11) + p_0**2*electric_tetrahexacontapole_length**10*(2*pi*f)**14*relative_permittivity**5*relative_permeability**6*sqrt(relative_permittivity*relative_permeability)/(667180800*pi*epsilon_0*c**13) + p_0**2*magnetic_dotriacontapole_length**10*(2*pi*f)**14*relative_permittivity**5*relative_permeability**6*sqrt(relative_permittivity*relative_permeability)/(8316000*pi*epsilon_0*c**13))
        predictions.append({'P_rad': float(P_rad)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_005_gen15_20260728_105919 Reference Law

Target: `P_rad`

Input variables: `p_0`, `f`

Reference expression:

```text
P_rad = ((1 - uniform_ball_profile_fraction)*exp(-relative_permittivity*relative_permeability*(2*pi*f*source_width/c)**2*(1 + uniform_ball_profile_fraction*profile_component_width_contrast)/2) + 3*uniform_ball_profile_fraction*(sin(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)) - sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)*cos(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c)))/(sqrt(5*relative_permittivity*relative_permeability*(1 - (1 - uniform_ball_profile_fraction)*profile_component_width_contrast))*(2*pi*f*source_width/c))**3)**2*(p_0**2*(2*pi*f)**4*relative_permeability*sqrt(relative_permittivity*relative_permeability)/(12*pi*epsilon_0*c**3) + p_0**2*electric_quadrupole_length**2*(2*pi*f)**6*relative_permittivity*relative_permeability**2*sqrt(relative_permittivity*relative_permeability)/(1440*pi*epsilon_0*c**5) + p_0**2*magnetic_dipole_length**2*(2*pi*f)**6*relative_permittivity*relative_permeability**2*sqrt(relative_permittivity*relative_permeability)/(12*pi*epsilon_0*c**5) + p_0**2*electric_octupole_length**4*(2*pi*f)**8*relative_permittivity**2*relative_permeability**3*sqrt(relative_permittivity*relative_permeability)/(3780*pi*epsilon_0*c**7) + p_0**2*magnetic_quadrupole_length**4*(2*pi*f)**8*relative_permittivity**2*relative_permeability**3*sqrt(relative_permittivity*relative_permeability)/(1440*pi*epsilon_0*c**7) + p_0**2*electric_hexadecapole_length**6*(2*pi*f)**10*relative_permittivity**3*relative_permeability**4*sqrt(relative_permittivity*relative_permeability)/(145152*pi*epsilon_0*c**9) + p_0**2*magnetic_octupole_length**6*(2*pi*f)**10*relative_permittivity**3*relative_permeability**4*sqrt(relative_permittivity*relative_permeability)/(3780*pi*epsilon_0*c**9) + p_0**2*electric_dotriacontapole_length**8*(2*pi*f)**12*relative_permittivity**4*relative_permeability**5*sqrt(relative_permittivity*relative_permeability)/(8316000*pi*epsilon_0*c**11) + p_0**2*magnetic_hexadecapole_length**8*(2*pi*f)**12*relative_permittivity**4*relative_permeability**5*sqrt(relative_permittivity*relative_permeability)/(145152*pi*epsilon_0*c**11) + p_0**2*electric_tetrahexacontapole_length**10*(2*pi*f)**14*relative_permittivity**5*relative_permeability**6*sqrt(relative_permittivity*relative_permeability)/(667180800*pi*epsilon_0*c**13) + p_0**2*magnetic_dotriacontapole_length**10*(2*pi*f)**14*relative_permittivity**5*relative_permeability**6*sqrt(relative_permittivity*relative_permeability)/(8316000*pi*epsilon_0*c**13))
```

Fixed parameters: c=3e+08, epsilon_0=8.854e-12, relative_permittivity=1, relative_permeability=1, source_width=0.001, uniform_ball_profile_fraction=0.5, profile_component_width_contrast=0.1, magnetic_dipole_length=0.001, electric_quadrupole_length=0.001, magnetic_quadrupole_length=0.001, electric_octupole_length=0.001, magnetic_octupole_length=0.001, electric_hexadecapole_length=0.001, magnetic_hexadecapole_length=0.001, electric_dotriacontapole_length=0.001, magnetic_dotriacontapole_length=0.001, electric_tetrahexacontapole_length=0.001.
EOL
