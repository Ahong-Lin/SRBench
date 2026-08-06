#!/bin/bash
# Reference solution for m2_electromagnetism_0_009_gen15_20260728_105920

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
    electron_charge = -1.6021766340000001e-19
    electron_mass = 9.1093837139e-31
    electric_field_x = 2000.0
    magnetic_flux_density_z = 0.02
    magnetic_flux_density_gradient_y = 0.5
    magnetic_flux_density_curvature_y = 10.0
    magnetic_flux_density_third_derivative_y = 1000.0
    magnetic_flux_density_fourth_derivative_y = 10000.0
    magnetic_flux_density_fifth_derivative_y = 100000.0
    magnetic_flux_density_sixth_derivative_y = 1000000.0
    magnetic_flux_density_seventh_derivative_y = 10000000.0
    magnetic_flux_density_eighth_derivative_y = 100000000.0
    magnetic_flux_density_ninth_derivative_y = 1000000000.0
    speed_of_light = 299792458.0
    electron_magnetic_moment_z = -9.2847647043e-24
    magnetic_flux_density_fringe_amplitude = -0.001
    magnetic_fringe_length_scale_y = 1e-06
    electron_radiation_reaction_time = 6.2623e-24
    magnetic_flux_density_asymmetric_fringe_amplitude = 0.01
    magnetic_asymmetric_fringe_length_scale_y = 1e-08

    for point in input_data:
        t = point['t']
        v_x = point['v_x']
        v_y = point['v_y']
        y_position = point['y_position']
        dv_x_dt = sqrt(1 - (v_x**2 + v_y**2)/speed_of_light**2)*(electron_charge*(electric_field_x*(1 - v_x**2/speed_of_light**2) + v_y*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11))) - electron_magnetic_moment_z*v_x*v_y*(magnetic_flux_density_gradient_y + magnetic_flux_density_curvature_y*y_position + magnetic_flux_density_third_derivative_y*y_position**2/2 + magnetic_flux_density_fourth_derivative_y*y_position**3/6 + magnetic_flux_density_fifth_derivative_y*y_position**4/24 + magnetic_flux_density_sixth_derivative_y*y_position**5/120 + magnetic_flux_density_seventh_derivative_y*y_position**6/720 + magnetic_flux_density_eighth_derivative_y*y_position**7/5040 + magnetic_flux_density_ninth_derivative_y*y_position**8/40320 - 10*magnetic_flux_density_fringe_amplitude*y_position**9*exp(-(y_position/magnetic_fringe_length_scale_y)**10)/magnetic_fringe_length_scale_y**10 + 11*magnetic_flux_density_asymmetric_fringe_amplitude*y_position**10*(1 - tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)**2)/magnetic_asymmetric_fringe_length_scale_y**11)/speed_of_light**2 - electron_radiation_reaction_time*electron_charge**2*v_x*((electric_field_x + v_y*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)))**2 + (v_x*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)))**2 - (electric_field_x*v_x/speed_of_light)**2)/(electron_mass*speed_of_light**2) + electron_radiation_reaction_time*electron_charge*v_y**2*(magnetic_flux_density_gradient_y + magnetic_flux_density_curvature_y*y_position + magnetic_flux_density_third_derivative_y*y_position**2/2 + magnetic_flux_density_fourth_derivative_y*y_position**3/6 + magnetic_flux_density_fifth_derivative_y*y_position**4/24 + magnetic_flux_density_sixth_derivative_y*y_position**5/120 + magnetic_flux_density_seventh_derivative_y*y_position**6/720 + magnetic_flux_density_eighth_derivative_y*y_position**7/5040 + magnetic_flux_density_ninth_derivative_y*y_position**8/40320 - 10*magnetic_flux_density_fringe_amplitude*y_position**9*exp(-(y_position/magnetic_fringe_length_scale_y)**10)/magnetic_fringe_length_scale_y**10 + 11*magnetic_flux_density_asymmetric_fringe_amplitude*y_position**10*(1 - tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)**2)/magnetic_asymmetric_fringe_length_scale_y**11)/sqrt(1 - (v_x**2 + v_y**2)/speed_of_light**2))/electron_mass
        predictions.append({'dv_x_dt': float(dv_x_dt)})

    return predictions
EOL

cat > /app/explain.md << 'EOL'
# m2_electromagnetism_0_009_gen15_20260728_105920 Reference Law

Target: `dv_x_dt`

Input variables: `t`, `v_x`, `v_y`, `y_position`

Reference expression:

```text
dv_x_dt = sqrt(1 - (v_x**2 + v_y**2)/speed_of_light**2)*(electron_charge*(electric_field_x*(1 - v_x**2/speed_of_light**2) + v_y*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11))) - electron_magnetic_moment_z*v_x*v_y*(magnetic_flux_density_gradient_y + magnetic_flux_density_curvature_y*y_position + magnetic_flux_density_third_derivative_y*y_position**2/2 + magnetic_flux_density_fourth_derivative_y*y_position**3/6 + magnetic_flux_density_fifth_derivative_y*y_position**4/24 + magnetic_flux_density_sixth_derivative_y*y_position**5/120 + magnetic_flux_density_seventh_derivative_y*y_position**6/720 + magnetic_flux_density_eighth_derivative_y*y_position**7/5040 + magnetic_flux_density_ninth_derivative_y*y_position**8/40320 - 10*magnetic_flux_density_fringe_amplitude*y_position**9*exp(-(y_position/magnetic_fringe_length_scale_y)**10)/magnetic_fringe_length_scale_y**10 + 11*magnetic_flux_density_asymmetric_fringe_amplitude*y_position**10*(1 - tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)**2)/magnetic_asymmetric_fringe_length_scale_y**11)/speed_of_light**2 - electron_radiation_reaction_time*electron_charge**2*v_x*((electric_field_x + v_y*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)))**2 + (v_x*(magnetic_flux_density_z + magnetic_flux_density_gradient_y*y_position + magnetic_flux_density_curvature_y*y_position**2/2 + magnetic_flux_density_third_derivative_y*y_position**3/6 + magnetic_flux_density_fourth_derivative_y*y_position**4/24 + magnetic_flux_density_fifth_derivative_y*y_position**5/120 + magnetic_flux_density_sixth_derivative_y*y_position**6/720 + magnetic_flux_density_seventh_derivative_y*y_position**7/5040 + magnetic_flux_density_eighth_derivative_y*y_position**8/40320 + magnetic_flux_density_ninth_derivative_y*y_position**9/362880 + magnetic_flux_density_fringe_amplitude*(exp(-(y_position/magnetic_fringe_length_scale_y)**10) - 1) + magnetic_flux_density_asymmetric_fringe_amplitude*tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)))**2 - (electric_field_x*v_x/speed_of_light)**2)/(electron_mass*speed_of_light**2) + electron_radiation_reaction_time*electron_charge*v_y**2*(magnetic_flux_density_gradient_y + magnetic_flux_density_curvature_y*y_position + magnetic_flux_density_third_derivative_y*y_position**2/2 + magnetic_flux_density_fourth_derivative_y*y_position**3/6 + magnetic_flux_density_fifth_derivative_y*y_position**4/24 + magnetic_flux_density_sixth_derivative_y*y_position**5/120 + magnetic_flux_density_seventh_derivative_y*y_position**6/720 + magnetic_flux_density_eighth_derivative_y*y_position**7/5040 + magnetic_flux_density_ninth_derivative_y*y_position**8/40320 - 10*magnetic_flux_density_fringe_amplitude*y_position**9*exp(-(y_position/magnetic_fringe_length_scale_y)**10)/magnetic_fringe_length_scale_y**10 + 11*magnetic_flux_density_asymmetric_fringe_amplitude*y_position**10*(1 - tanh((y_position/magnetic_asymmetric_fringe_length_scale_y)**11)**2)/magnetic_asymmetric_fringe_length_scale_y**11)/sqrt(1 - (v_x**2 + v_y**2)/speed_of_light**2))/electron_mass
```

Fixed parameters: electron_charge=-1.60218e-19, electron_mass=9.10938e-31, electric_field_x=2000, magnetic_flux_density_z=0.02, magnetic_flux_density_gradient_y=0.5, magnetic_flux_density_curvature_y=10, magnetic_flux_density_third_derivative_y=1000, magnetic_flux_density_fourth_derivative_y=10000, magnetic_flux_density_fifth_derivative_y=100000, magnetic_flux_density_sixth_derivative_y=1e+06, magnetic_flux_density_seventh_derivative_y=1e+07, magnetic_flux_density_eighth_derivative_y=1e+08, magnetic_flux_density_ninth_derivative_y=1e+09, speed_of_light=2.99792e+08, electron_magnetic_moment_z=-9.28476e-24, magnetic_flux_density_fringe_amplitude=-0.001, magnetic_fringe_length_scale_y=1e-06, electron_radiation_reaction_time=6.2623e-24, magnetic_flux_density_asymmetric_fringe_amplitude=0.01, magnetic_asymmetric_fringe_length_scale_y=1e-08.
EOL
